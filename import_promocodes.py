"""
Import promo codes from WordPress-exported MD files into the database.
Generates SQL file and can also insert directly via API or raw SQL.

Usage:
    python import_promocodes.py --sql     # Generate SQL INSERT file
    python import_promocodes.py --api     # Insert via API (requires running backend)
"""
import re
import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_FILES = [
    os.path.join(BASE_DIR, f"promocodes{s}.md")
    for s in ["", "2", "3", "4", "5"]
]

MONTH_MAP = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4,
    "мая": 5, "июня": 6, "июля": 7, "августа": 8,
    "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def parse_date(raw: str) -> Optional[str]:
    raw = raw.strip().rstrip(".")
    if not raw or raw == "–" or raw == "-":
        return None
    m = re.match(r"(\d{1,2})\s+(\S+),?\s+(\d{4})", raw)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2).lower().rstrip(",")
    year = int(m.group(3))
    month = MONTH_MAP.get(month_name)
    if not month:
        return None
    try:
        dt = datetime(year, month, day, 23, 59, 59)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def parse_usage(raw: str) -> Tuple[int, Optional[int]]:
    raw = raw.strip()
    parts = raw.split("/")
    if len(parts) != 2:
        return 0, None
    used = int(parts[0].strip())
    max_part = parts[1].strip()
    if max_part in ("∞", "~", "inf", ""):
        return used, None
    try:
        return used, int(max_part)
    except ValueError:
        return used, None


def parse_discount_type(raw: str) -> Optional[str]:
    raw = raw.strip().lower()
    if "процент" in raw:
        return "percentage"
    if "фиксированн" in raw:
        return "fixed"
    return None


def parse_md_file(filepath: str) -> List[Dict]:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    promos = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("Выбрать ") and "\t" in line:
            parts = line.split("\t", 1)
            code_display = parts[0].replace("Выбрать ", "").strip()
            code_lower = parts[1].strip() if len(parts) > 1 else code_display.lower()
            code = code_display.upper()

            i += 1
            if i < len(lines) and "Изменить" in lines[i]:
                i += 1

            if i < len(lines):
                data_line = lines[i].strip()
                fields = data_line.split("\t")
                if len(fields) >= 3:
                    discount_type = parse_discount_type(fields[0])
                    if not discount_type:
                        i += 1
                        continue
                    try:
                        discount_value = float(fields[1].strip().replace(",", "."))
                    except ValueError:
                        i += 1
                        continue

                    description = ""
                    if len(fields) > 2:
                        desc = fields[2].strip()
                        if desc and desc != "–" and desc != "-":
                            description = desc

                    used_count = 0
                    max_uses = None
                    if len(fields) > 4:
                        usage_raw = fields[4].strip()
                        if "/" in usage_raw:
                            used_count, max_uses = parse_usage(usage_raw)

                    expires_at = None
                    if len(fields) > 5:
                        expires_at = parse_date(fields[5])

                    promos.append({
                        "code": code,
                        "discount_type": discount_type,
                        "discount_value": discount_value,
                        "description": description,
                        "max_uses": max_uses,
                        "used_count": used_count,
                        "expires_at": expires_at,
                    })
        i += 1

    return promos


def deduplicate(promos: List[Dict]) -> List[Dict]:
    seen = {}
    for p in promos:
        key = p["code"]
        if key not in seen:
            seen[key] = p
        else:
            existing = seen[key]
            if (p["used_count"] or 0) > (existing["used_count"] or 0):
                seen[key] = p
    return list(seen.values())


def escape_sql(val: str) -> str:
    return val.replace("'", "''")


def generate_sql(promos: List[Dict]) -> str:
    lines = [
        "-- Auto-generated promo code import",
        f"-- Total: {len(promos)} codes",
        f"-- Generated: {datetime.now().isoformat()}",
        "",
    ]
    for p in promos:
        code = escape_sql(p["code"])
        desc = escape_sql(p["description"])
        expires = f"'{p['expires_at']}'" if p["expires_at"] else "NULL"
        max_uses = str(p["max_uses"]) if p["max_uses"] is not None else "NULL"
        lines.append(
            f"INSERT INTO promo_codes (code, discount_type, discount_value, description, max_uses, used_count, is_active, expires_at) "
            f"VALUES ('{code}', '{p['discount_type']}', {p['discount_value']}, '{desc}', {max_uses}, {p['used_count']}, true, {expires}) "
            f"ON CONFLICT (code) DO NOTHING;"
        )
    return "\n".join(lines)


def main():
    mode = "--sql"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    all_promos = []
    for f in MD_FILES:
        parsed = parse_md_file(f)
        print(f"Parsed {os.path.basename(f)}: {len(parsed)} codes")
        all_promos.extend(parsed)

    promos = deduplicate(all_promos)
    print(f"\nTotal unique codes: {len(promos)}")

    if mode == "--sql":
        sql = generate_sql(promos)
        out_path = os.path.join(BASE_DIR, "migrations", "import_promo_codes.sql")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql)
        print(f"SQL written to: {out_path}")

    elif mode == "--json":
        out_path = os.path.join(BASE_DIR, "promo_codes_import.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(promos, f, ensure_ascii=False, indent=2)
        print(f"JSON written to: {out_path}")

    elif mode == "--api":
        try:
            import requests
        except ImportError:
            print("Install requests: pip install requests")
            return
        api_url = os.getenv("CATALOG_API_URL", "http://localhost:8000")
        token = os.getenv("CATALOG_AUTH_TOKEN", "")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        created = 0
        skipped = 0
        for p in promos:
            body = {
                "code": p["code"],
                "discount_type": p["discount_type"],
                "discount_value": p["discount_value"],
                "description": p["description"],
                "max_uses": p["max_uses"],
                "expires_at": p["expires_at"],
            }
            try:
                resp = requests.post(f"{api_url}/api/promocodes", json=body, headers=headers, timeout=10)
                if resp.status_code in (200, 201):
                    created += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"Error for {p['code']}: {e}")
                skipped += 1
        print(f"Created: {created}, Skipped: {skipped}")

    else:
        print("Usage: python import_promocodes.py [--sql|--json|--api]")


if __name__ == "__main__":
    main()
