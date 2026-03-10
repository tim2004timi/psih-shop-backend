from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.promocode import PromoCode, DiscountType
from src.schemas.promocode import PromoCodeCreate, PromoCodeUpdate, PromoCodeValidateResponse
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


async def create_promo_code(db: AsyncSession, data: PromoCodeCreate) -> PromoCode:
    promo = PromoCode(
        code=data.code.upper().strip(),
        discount_type=data.discount_type,
        discount_value=data.discount_value,
        description=data.description or "",
        max_uses=data.max_uses,
        expires_at=data.expires_at,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return promo


async def get_promo_codes(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PromoCode]:
    result = await db.execute(
        select(PromoCode).order_by(PromoCode.created_at.desc()).offset(skip).limit(limit)
    )
    return result.scalars().all()


async def get_promo_code_by_id(db: AsyncSession, promo_id: int) -> Optional[PromoCode]:
    result = await db.execute(select(PromoCode).where(PromoCode.id == promo_id))
    return result.scalar_one_or_none()


async def get_promo_code_by_code(db: AsyncSession, code: str) -> Optional[PromoCode]:
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == code.upper().strip())
    )
    return result.scalar_one_or_none()


async def update_promo_code(db: AsyncSession, promo_id: int, data: PromoCodeUpdate) -> Optional[PromoCode]:
    promo = await get_promo_code_by_id(db, promo_id)
    if not promo:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(promo, field, value)
    await db.commit()
    await db.refresh(promo)
    return promo


async def delete_promo_code(db: AsyncSession, promo_id: int) -> bool:
    promo = await get_promo_code_by_id(db, promo_id)
    if not promo:
        return False
    await db.delete(promo)
    await db.commit()
    return True


async def validate_promo_code(db: AsyncSession, code: str, order_amount: Decimal) -> PromoCodeValidateResponse:
    promo = await get_promo_code_by_code(db, code)

    if not promo:
        return PromoCodeValidateResponse(valid=False, message="Промокод не найден")

    if not promo.is_active:
        return PromoCodeValidateResponse(valid=False, message="Промокод неактивен")

    if promo.expires_at and promo.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        return PromoCodeValidateResponse(valid=False, message="Срок действия промокода истек")

    if promo.max_uses and promo.used_count >= promo.max_uses:
        return PromoCodeValidateResponse(valid=False, message="Промокод исчерпан")

    if promo.discount_type == DiscountType.PERCENTAGE:
        discount_amount = (order_amount * promo.discount_value / Decimal("100")).quantize(Decimal("0.01"))
    else:
        discount_amount = min(promo.discount_value, order_amount)

    return PromoCodeValidateResponse(
        valid=True,
        discount_type=promo.discount_type,
        discount_value=promo.discount_value,
        discount_amount=discount_amount,
        message="Промокод применен"
    )


async def increment_promo_usage(db: AsyncSession, promo_id: int) -> None:
    promo = await get_promo_code_by_id(db, promo_id)
    if promo:
        promo.used_count = (promo.used_count or 0) + 1
        await db.commit()
