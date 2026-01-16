from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Set
from src.models.category import Category, ProductCategory
from src.models.product import Product, ProductColor


async def create_category(db: AsyncSession, *, name: str, slug: str, parent_id: Optional[int], level: int, sort_order: int, is_active: bool) -> Category:
    cat = Category(name=name, slug=slug, parent_id=parent_id, level=level, sort_order=sort_order, is_active=is_active)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


async def delete_category(db: AsyncSession, category_id: int) -> bool:
    result = await db.execute(select(Category).where(Category.id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        return False
    db.delete(cat)
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


async def get_products_by_category_slug(db: AsyncSession, slug: str) -> List[ProductColor]:
    """Получить продукты категории (теперь возвращаем ProductColor)"""
    cat = await get_category_by_slug(db, slug)
    if not cat:
        return []

    categories_result = await db.execute(
        select(Category.id, Category.parent_id).where(Category.is_active == True)
    )
    rows = categories_result.all()
    children: Dict[int, List[int]] = {}
    for cid, parent_id in rows:
        if parent_id is None:
            continue
        children.setdefault(parent_id, []).append(cid)

    category_ids: Set[int] = set()
    stack = [cat.id]
    while stack:
        current = stack.pop()
        if current in category_ids:
            continue
        category_ids.add(current)
        stack.extend(children.get(current, []))

    result = await db.execute(
        select(ProductColor)
        .join(Product, ProductColor.product_id == Product.id)
        .join(ProductCategory, ProductCategory.product_id == Product.id)
        .where(ProductCategory.category_id.in_(list(category_ids)))
        .order_by(ProductCategory.sort_order)
    )
    return result.scalars().all()


async def check_category_assignment_collision(db: AsyncSession, product_id: int, category_id: int) -> Optional[str]:
    """
    Check if assigning product to category would cause slug collision.
    Returns the conflicting slug if any, else None.
    """
    result = await db.execute(
        select(ProductColor.slug).where(ProductColor.product_id == product_id)
    )
    slugs = result.scalars().all()
    
    if not slugs:
        return None
        
    query = (
        select(ProductColor.slug)
        .join(Product, ProductColor.product_id == Product.id)
        .join(ProductCategory, ProductCategory.product_id == Product.id)
        .where(
            ProductCategory.category_id == category_id,
            ProductColor.slug.in_(slugs),
            Product.id != product_id
        )
    )
    
    result = await db.execute(query)
    return result.scalar_one_or_none()

async def add_product_to_category(db: AsyncSession, product_id: int, category_id: int) -> bool:
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


async def remove_product_from_category(db: AsyncSession, product_id: int, category_id: int) -> bool:
    result = await db.execute(
        select(ProductCategory).where(
            ProductCategory.product_id == product_id,
            ProductCategory.category_id == category_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        return False
    db.delete(link)
    await db.commit()
    return True


async def set_product_categories(db: AsyncSession, product_id: int, category_ids: List[int]) -> bool:
    """Установить список категорий для товара (удаляет старые и добавляет новые)"""
    # Удаляем все текущие привязки
    from sqlalchemy import delete
    await db.execute(
        delete(ProductCategory).where(ProductCategory.product_id == product_id)
    )
    
    # Добавляем новые
    for cat_id in category_ids:
        link = ProductCategory(product_id=product_id, category_id=cat_id)
        db.add(link)
        
    await db.commit()
    return True


async def get_categories_by_product(db: AsyncSession, product_id: int) -> List[Category]:
    """Получить все категории, к которым привязан продукт"""
    result = await db.execute(
        select(Category)
        .join(ProductCategory, ProductCategory.category_id == Category.id)
        .where(ProductCategory.product_id == product_id)
    )
    return result.scalars().all()


async def reorder_category_products(db: AsyncSession, category_id: int, product_ids: List[int]) -> bool:
    """Изменить порядок товаров в категории"""
    # Получаем все связи для данной категории
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.category_id == category_id)
    )
    links = {link.product_id: link for link in result.scalars().all()}
    
    # Обновляем sort_order для тех, что переданы в списке
    for index, prod_id in enumerate(product_ids):
        if prod_id in links:
            links[prod_id].sort_order = index
            
    await db.commit()
    return True


