from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from src.models.category import Category, ProductCategory
from src.models.product import Product


async def create_category(db: AsyncSession, *, id: str, name: str, slug: str, parent_id: Optional[str], level: int, sort_order: int, is_active: bool) -> Category:
    cat = Category(id=id, name=name, slug=slug, parent_id=parent_id, level=level, sort_order=sort_order, is_active=is_active)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, category_id: str) -> bool:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        return False
    await db.delete(cat)
    await db.commit()
    return True


async def get_all_categories(db: AsyncSession) -> List[Category]:
    result = await db.execute(select(Category).where(Category.is_active == True).order_by(Category.level, Category.sort_order, Category.name))
    return result.scalars().all()


def build_tree(categories: List[Category]) -> List[Dict]:
    by_id = {c.id: {"id": c.id, "name": c.name, "slug": c.slug, "children": []} for c in categories}
    roots: List[Dict] = []
    for c in categories:
        node = by_id[c.id]
        if c.parent_id and c.parent_id in by_id:
            by_id[c.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


async def get_category_by_slug(db: AsyncSession, slug: str) -> Optional[Category]:
    result = await db.execute(select(Category).where(Category.slug == slug))
    return result.scalar_one_or_none()


async def get_products_by_category_slug(db: AsyncSession, slug: str) -> List[Product]:
    cat = await get_category_by_slug(db, slug)
    if not cat:
        return []
    result = await db.execute(
        select(Product)
        .join(ProductCategory, ProductCategory.product_id == Product.id)
        .where(ProductCategory.category_id == cat.id)
    )
    return result.scalars().all()


async def add_product_to_category(db: AsyncSession, product_id: str, category_id: str) -> bool:
    # check duplicates
    exists = await db.execute(
        select(ProductCategory).where(
            ProductCategory.product_id == product_id,
            ProductCategory.category_id == category_id,
        )
    )
    if exists.scalar_one_or_none():
        return True
    link = ProductCategory(product_id=product_id, category_id=category_id)
    db.add(link)
    await db.commit()
    return True


async def remove_product_from_category(db: AsyncSession, product_id: str, category_id: str) -> bool:
    result = await db.execute(
        select(ProductCategory).where(
            ProductCategory.product_id == product_id,
            ProductCategory.category_id == category_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        return False
    await db.delete(link)
    await db.commit()
    return True


