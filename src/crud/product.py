from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product, ProductColor, ProductSize, ProductImage
from src.schemas.product import ProductCreate, ProductUpdate, ProductColorCreate, ProductColorUpdate
from typing import List, Optional
from collections import defaultdict

# --- Product CRUD ---
async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Получить продукт по ID"""
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()

async def get_product_by_slug(db: AsyncSession, slug: str) -> Optional[ProductColor]:
    """Получить продукт по slug (теперь ищем в ProductColor)"""
    result = await db.execute(select(ProductColor).where(ProductColor.slug == slug))
    return result.scalar_one_or_none()

async def get_products(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[ProductColor]:
    """Получить список продуктов (теперь возвращаем ProductColor)"""
    query = select(ProductColor).join(Product, ProductColor.product_id == Product.id)
    
    if status:
        query = query.where(Product.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (ProductColor.title.ilike(search_filter)) |
            (ProductColor.slug.ilike(search_filter)) |
            (Product.description.ilike(search_filter))
        )
    
    query = query.offset(skip).limit(limit).order_by(ProductColor.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()

async def get_products_count(
    db: AsyncSession,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> int:
    """Получить общее количество продуктов"""
    query = select(func.count(ProductColor.id)).join(Product, ProductColor.product_id == Product.id)
    
    if status:
        query = query.where(Product.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (ProductColor.title.ilike(search_filter)) |
            (ProductColor.slug.ilike(search_filter)) |
            (Product.description.ilike(search_filter))
        )
    
    result = await db.execute(query)
    return result.scalar()

async def create_product(db: AsyncSession, product_create: ProductCreate) -> Product:
    """Создать новый продукт"""
    db_product = Product(
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

async def update_product(db: AsyncSession, product_id: int, update_data: ProductUpdate) -> Optional[Product]:
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

async def delete_product(db: AsyncSession, product_id: int) -> bool:
    """Удалить продукт"""
    product = await get_product_by_id(db, product_id)
    if not product:
        return False
    
    await db.delete(product)
    await db.commit()
    return True

async def check_slug_exists(db: AsyncSession, slug: str, exclude_id: Optional[int] = None) -> bool:
    """Проверить, существует ли slug (теперь в ProductColor)"""
    query = select(ProductColor).where(ProductColor.slug == slug)
    if exclude_id:
        query = query.where(ProductColor.id != exclude_id)
    
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None

# --- ProductColor CRUD ---
async def get_product_color_by_id(db: AsyncSession, color_id: int) -> Optional[ProductColor]:
    """Получить цвет продукта по ID"""
    result = await db.execute(select(ProductColor).where(ProductColor.id == color_id))
    return result.scalar_one_or_none()

async def list_product_colors(db: AsyncSession, product_id: int) -> List[ProductColor]:
    """Получить список цветов продукта"""
    result = await db.execute(select(ProductColor).where(ProductColor.product_id == product_id))
    return result.scalars().all()

async def create_product_color(db: AsyncSession, product_id: int, *, slug: str, title: str, label: str, hex: str) -> ProductColor:
    """Создать цвет продукта"""
    color = ProductColor(product_id=product_id, slug=slug, title=title, label=label, hex=hex)
    db.add(color)
    await db.commit()
    await db.refresh(color)
    return color

async def update_product_color(db: AsyncSession, color_id: int, update_data: ProductColorUpdate) -> Optional[ProductColor]:
    """Обновить цвет продукта"""
    color = await get_product_color_by_id(db, color_id)
    if not color:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(color, field, value)
    
    await db.commit()
    await db.refresh(color)
    return color

async def delete_product_color(db: AsyncSession, color_id: int) -> bool:
    """Удалить цвет продукта"""
    result = await db.execute(select(ProductColor).where(ProductColor.id == color_id))
    color = result.scalar_one_or_none()
    if not color:
        return False
    await db.delete(color)
    await db.commit()
    return True

# --- ProductImage CRUD ---
async def list_product_images(db: AsyncSession, product_color_id: int) -> List[ProductImage]:
    """Получить список изображений продукта по цвету"""
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_color_id == product_color_id)
        .order_by(ProductImage.sort_order)
    )
    return result.scalars().all()

async def create_product_image(db: AsyncSession, product_color_id: int, *, file_url: str, sort_order: int = 0) -> ProductImage:
    """Создать изображение продукта"""
    img = ProductImage(product_color_id=product_color_id, file=file_url, sort_order=sort_order)
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return img

async def delete_product_image(db: AsyncSession, image_id: int) -> bool:
    """Удалить изображение продукта"""
    result = await db.execute(select(ProductImage).where(ProductImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        return False
    await db.delete(img)
    await db.commit()
    return True

async def get_images_for_products(db: AsyncSession, product_color_ids: List[int]) -> dict[int, list[ProductImage]]:
    """Загрузить изображения для набора продуктов и сгруппировать по product_color_id"""
    if not product_color_ids:
        return {}
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_color_id.in_(product_color_ids))
        .order_by(ProductImage.sort_order)
    )
    grouped: dict[int, list[ProductImage]] = defaultdict(list)
    for image in result.scalars().all():
        grouped[image.product_color_id].append(image)
    return grouped

# --- ProductSize CRUD ---
async def list_product_sizes(db: AsyncSession, product_color_id: int) -> List[ProductSize]:
    """Получить список размеров продукта по цвету"""
    result = await db.execute(
        select(ProductSize)
        .where(ProductSize.product_color_id == product_color_id)
        .order_by(ProductSize.size)
    )
    return result.scalars().all()

async def create_product_size(db: AsyncSession, product_color_id: int, *, size: str, quantity: int = 0) -> ProductSize:
    """Создать размер продукта"""
    ps = ProductSize(product_color_id=product_color_id, size=size, quantity=quantity)
    db.add(ps)
    await db.commit()
    await db.refresh(ps)
    return ps

async def update_product_size(db: AsyncSession, size_id: int, *, size: Optional[str] = None, quantity: Optional[int] = None) -> Optional[ProductSize]:
    """Обновить размер продукта"""
    result = await db.execute(select(ProductSize).where(ProductSize.id == size_id))
    ps = result.scalar_one_or_none()
    if not ps:
        return None
    
    if size is not None:
        ps.size = size
    if quantity is not None:
        ps.quantity = quantity
    
    await db.commit()
    await db.refresh(ps)
    return ps

async def delete_product_size(db: AsyncSession, size_id: int) -> bool:
    """Удалить размер продукта"""
    result = await db.execute(select(ProductSize).where(ProductSize.id == size_id))
    ps = result.scalar_one_or_none()
    if not ps:
        return False
    await db.delete(ps)
    await db.commit()
    return True

async def get_sizes_for_products(db: AsyncSession, product_color_ids: List[int]) -> dict[int, list[dict]]:
    """Загрузить размеры для набора продуктов и сгруппировать по product_color_id"""
    if not product_color_ids:
        return {}
    result = await db.execute(
        select(ProductSize).where(ProductSize.product_color_id.in_(product_color_ids))
    )
    grouped: dict[int, list[dict]] = defaultdict(list)
    for size in result.scalars().all():
        grouped[size.product_color_id].append({
            "id": size.id,
            "size": size.size,
            "quantity": size.quantity
        })
    return grouped
