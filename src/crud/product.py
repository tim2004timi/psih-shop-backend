from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product, ProductColor, ProductSize, ProductImage
from src.schemas.product import ProductCreate, ProductUpdate
from typing import List, Optional
from collections import defaultdict

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

async def list_product_images(db: AsyncSession, product_id: str) -> List[ProductImage]:
    result = await db.execute(select(ProductImage).where(ProductImage.product_id == product_id).order_by(ProductImage.sort_order))
    return result.scalars().all()

async def create_product_image(db: AsyncSession, product_id: str, *, id: str, file_url: str, sort_order: int = 0) -> ProductImage:
    img = ProductImage(id=id, product_id=product_id, file=file_url, sort_order=sort_order)
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return img

async def delete_product_image(db: AsyncSession, image_id: str) -> bool:
    result = await db.execute(select(ProductImage).where(ProductImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        return False
    await db.delete(img)
    await db.commit()
    return True

async def get_colors_for_products(db: AsyncSession, product_ids: List[str]) -> dict[str, list[dict]]:
    """Загрузить цвета для набора продуктов и сгруппировать по product_id"""
    if not product_ids:
        return {}
    result = await db.execute(
        select(ProductColor).where(ProductColor.product_id.in_(product_ids))
    )
    grouped: dict[str, list[dict]] = defaultdict(list)
    for color in result.scalars().all():
        grouped[color.product_id].append({
            "code": color.code,
            "label": color.label,
            "hex": color.hex,
        })
    return grouped

async def get_sizes_for_products(db: AsyncSession, product_ids: List[str]) -> dict[str, list[str]]:
    """Загрузить размеры для набора продуктов и сгруппировать по product_id"""
    if not product_ids:
        return {}
    result = await db.execute(
        select(ProductSize).where(ProductSize.product_id.in_(product_ids))
    )
    grouped: dict[str, list[str]] = defaultdict(list)
    for size in result.scalars().all():
        grouped[size.product_id].append(size.size)
    return grouped

# --- CRUD for colors ---
async def list_product_colors(db: AsyncSession, product_id: str) -> List[ProductColor]:
    result = await db.execute(select(ProductColor).where(ProductColor.product_id == product_id))
    return result.scalars().all()

async def create_product_color(db: AsyncSession, product_id: str, *, id: str, code: str, label: str, hex: str) -> ProductColor:
    color = ProductColor(id=id, product_id=product_id, code=code, label=label, hex=hex)
    db.add(color)
    await db.commit()
    await db.refresh(color)
    return color

async def delete_product_color(db: AsyncSession, color_id: str) -> bool:
    result = await db.execute(select(ProductColor).where(ProductColor.id == color_id))
    color = result.scalar_one_or_none()
    if not color:
        return False
    await db.delete(color)
    await db.commit()
    return True

# --- CRUD for sizes ---
async def list_product_sizes(db: AsyncSession, product_id: str) -> List[ProductSize]:
    result = await db.execute(select(ProductSize).where(ProductSize.product_id == product_id))
    return result.scalars().all()

async def create_product_size(db: AsyncSession, product_id: str, *, id: str, size: str) -> ProductSize:
    ps = ProductSize(id=id, product_id=product_id, size=size)
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return ps

async def delete_product_size(db: AsyncSession, size_id: str) -> bool:
    result = await db.execute(select(ProductSize).where(ProductSize.id == size_id))
    ps = result.scalar_one_or_none()
    if not ps:
        return False
    await db.delete(ps)
    await db.commit()
    return True

async def create_product(db: AsyncSession, product_create: ProductCreate) -> Product:
    """Создать новый продукт"""
    db_product = Product(
        id=product_create.id,
        slug=product_create.slug,
        title=product_create.title,
        description=product_create.description,
        price=product_create.price,
        discount_price=product_create.discount_price,
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
