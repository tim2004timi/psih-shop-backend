from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product
from src.schemas.product import ProductCreate, ProductUpdate
from typing import List, Optional

async def get_product_by_id(db: AsyncSession, product_id: str) -> Optional[Product]:
    """Получить продукт по ID"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_product_by_slug(db: AsyncSession, slug: str) -> Optional[Product]:
    """Получить продукт по slug"""
    result = await db.execute(select(Product).where(Product.slug == slug))
    return result.scalar_one_or_none()

async def get_products(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Product]:
    """Получить список продуктов с фильтрацией"""
    query = select(Product)
    
    if status:
        query = query.where(Product.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Product.title.ilike(search_filter)) |
            (Product.description.ilike(search_filter))
        )
    
    query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_products_count(
    db: AsyncSession,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> int:
    """Получить общее количество продуктов"""
    query = select(func.count(Product.id))
    
    if status:
        query = query.where(Product.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Product.title.ilike(search_filter)) |
            (Product.description.ilike(search_filter))
        )
    
    result = await db.execute(query)
    return result.scalar()

async def create_product(db: AsyncSession, product_create: ProductCreate) -> Product:
    """Создать новый продукт"""
    db_product = Product(
        id=product_create.id,
        slug=product_create.slug,
        title=product_create.title,
        description=product_create.description,
        price=product_create.price,
        currency=product_create.currency,
        composition=product_create.composition,
        fit=product_create.fit,
        status=product_create.status,
        is_pre_order=product_create.is_pre_order,
        meta_care=product_create.meta_care,
        meta_shipping=product_create.meta_shipping,
        meta_returns=product_create.meta_returns
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

async def update_product(db: AsyncSession, product_id: str, update_data: ProductUpdate) -> Optional[Product]:
    """Обновить продукт"""
    product = await get_product_by_id(db, product_id)
    if not product:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(product, field, value)
    
    await db.commit()
    await db.refresh(product)
    return product

async def delete_product(db: AsyncSession, product_id: str) -> bool:
    """Удалить продукт"""
    product = await get_product_by_id(db, product_id)
    if not product:
        return False
    
    await db.delete(product)
    await db.commit()
    return True

async def check_slug_exists(db: AsyncSession, slug: str, exclude_id: Optional[str] = None) -> bool:
    """Проверить, существует ли slug"""
    query = select(Product).where(Product.slug == slug)
    if exclude_id:
        query = query.where(Product.id != exclude_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None
