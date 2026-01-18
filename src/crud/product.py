from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.product import Product, ProductColor, ProductSize, ProductImage, ProductSection
from src.models.category import Category, ProductCategory
from src.schemas.product import (
    ProductCreate, ProductUpdate, ProductColorCreate, ProductColorUpdate,
    ProductSectionCreate, ProductSectionUpdate
)
from src.utils import delete_image_from_minio
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
    return result.scalars().first()

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
        weight=product_create.weight,
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
    """Удалить продукт со всеми цветами и изображениями"""
    product = await db.get(Product, product_id)
    if not product:
        return False
    
    # Получаем все цвета продукта
    result = await db.execute(select(ProductColor).where(ProductColor.product_id == product_id))
    colors = result.scalars().all()
    
    for color in colors:
        # Для каждого цвета удаляем его изображения из хранилища
        img_result = await db.execute(select(ProductImage).where(ProductImage.product_color_id == color.id))
        images = img_result.scalars().all()
        for img in images:
            if img.file:
                await delete_image_from_minio(img.file)
    
    await db.delete(product)
    await db.commit()
    return True

async def check_slug_exists(db: AsyncSession, slug: str, exclude_id: Optional[int] = None) -> bool:
    """Проверить, существует ли slug (теперь в ProductColor)"""
    query = select(ProductColor).where(ProductColor.slug == slug)
    if exclude_id:
        query = query.where(ProductColor.id != exclude_id)
    
    result = await db.execute(query)
    return result.scalars().first() is not None

async def check_slug_collision(db: AsyncSession, slug: str, product_id: int, exclude_color_id: Optional[int] = None) -> bool:
    """
    Check if slug conflicts with other products in the same categories.
    Returns True if collision exists.
    """
    result = await db.execute(
        select(ProductCategory.category_id).where(ProductCategory.product_id == product_id)
    )
    category_ids = result.scalars().all()
    
    if not category_ids:
        return False
        
    query = (
        select(ProductColor)
        .join(Product, ProductColor.product_id == Product.id)
        .join(ProductCategory, ProductCategory.product_id == Product.id)
        .where(
            ProductColor.slug == slug,
            ProductCategory.category_id.in_(category_ids),
            Product.id != product_id 
        )
    )
    
    if exclude_color_id:
        query = query.where(ProductColor.id != exclude_color_id)
    
    result = await db.execute(query)
    return result.scalars().first() is not None

async def get_product_by_category_and_slug(db: AsyncSession, category_slug: str, product_slug: str) -> Optional[ProductColor]:
    """Get product by category slug and product slug"""
    query = (
        select(ProductColor)
        .join(Product, ProductColor.product_id == Product.id)
        .join(ProductCategory, ProductCategory.product_id == Product.id)
        .join(Category, ProductCategory.category_id == Category.id)
        .where(
            Category.slug == category_slug,
            ProductColor.slug == product_slug
        )
    )
    result = await db.execute(query)
    
    return result.scalars().first()

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
    """Удалить цвет продукта и его изображения"""
    color = await db.get(ProductColor, color_id)
    if not color:
        return False
    
    # Удаляем изображения из хранилища
    img_result = await db.execute(select(ProductImage).where(ProductImage.product_color_id == color.id))
    images = img_result.scalars().all()
    for img in images:
        if img.file:
            await delete_image_from_minio(img.file)
            
    await db.delete(color)
    await db.commit()
    return True

# --- ProductImage CRUD ---
async def list_product_images(db: AsyncSession, product_color_id: int) -> List[ProductImage]:
    """Получить список изображений продукта по цвету (главное фото всегда первое)"""
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_color_id == product_color_id)
        .order_by(ProductImage.sort_order.desc(), ProductImage.id.asc())
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
    img = await db.get(ProductImage, image_id)
    if not img:
        return False
    
    # Сначала удаляем файл из хранилища
    if img.file:
        await delete_image_from_minio(img.file)
    
    await db.delete(img)
    await db.commit()
    return True

async def reorder_product_images(db: AsyncSession, product_color_id: int, image_ids: List[int]) -> bool:
    """Изменить порядок изображений продукта"""
    result = await db.execute(
        select(ProductImage).where(ProductImage.product_color_id == product_color_id)
    )
    images = {img.id: img for img in result.scalars().all()}
    
    for index, img_id in enumerate(image_ids):
        if img_id in images:
            images[img_id].sort_order = index
            
    await db.commit()
    return True

async def delete_primary_image(db: AsyncSession, product_color_id: int) -> bool:
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_color_id == product_color_id)
        .where(ProductImage.sort_order == 1000)
    )
    images = result.scalars().all()
    if not images:
        return False
    for img in images:
        if img.file:
            await delete_image_from_minio(img.file)
        await db.delete(img)
    await db.commit()
    return True

async def get_images_for_products(db: AsyncSession, product_color_ids: List[int]) -> dict[int, list[ProductImage]]:
    """Загрузить изображения для набора продуктов и сгруппировать по product_color_id (главное фото первое)"""
    if not product_color_ids:
        return {}
    result = await db.execute(
        select(ProductImage)
        .where(ProductImage.product_color_id.in_(product_color_ids))
        .order_by(ProductImage.sort_order.desc(), ProductImage.id.asc())
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
        .order_by(ProductSize.sort_order)
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
    ps = await db.get(ProductSize, size_id)
    if not ps:
        return False
    db.delete(ps)
    await db.commit()
    return True

async def get_product_main_category(db: AsyncSession, product_id: int) -> Optional[dict]:
    """Получить основную категорию продукта (уровень 0)"""
    # Получаем все категории, к которым привязан продукт
    query = (
        select(Category)
        .join(ProductCategory, ProductCategory.category_id == Category.id)
        .where(ProductCategory.product_id == product_id)
    )
    result = await db.execute(query)
    categories = result.scalars().all()
    
    if not categories:
        return None
        
    # Ищем самую верхнюю категорию (level 0)
    # Если продукт привязан к подкатегории, поднимаемся вверх по дереву
    for cat in categories:
        if cat.level == 0:
            return {"name": cat.name, "slug": cat.slug}
            
        current_cat = cat
        # Ограничим количество итераций на всякий случай, чтобы избежать бесконечного цикла
        for _ in range(10): 
            if current_cat.level == 0 or not current_cat.parent_id:
                break
            parent_query = select(Category).where(Category.id == current_cat.parent_id)
            parent_result = await db.execute(parent_query)
            parent_cat = parent_result.scalar_one_or_none()
            if not parent_cat:
                break
            current_cat = parent_cat
            
        if current_cat.level == 0:
            return {"name": current_cat.name, "slug": current_cat.slug}
            
    return None

async def get_main_categories_for_products(db: AsyncSession, product_ids: List[int]) -> dict[int, dict]:
    """Загрузить основные категории для списка продуктов (батч-версия)"""
    if not product_ids:
        return {}
        
    # Это упрощенная версия, которая делает запросы для каждого товара,
    # но в будущем её можно оптимизировать одним сложным CTE запросом.
    # Для текущего объема данных этого достаточно.
    results = {}
    for pid in product_ids:
        main_cat = await get_product_main_category(db, pid)
        if main_cat:
            results[pid] = main_cat
    return results

async def get_sizes_for_products(db: AsyncSession, product_color_ids: List[int]) -> dict[int, list[dict]]:
    """Загрузить размеры для набора продуктов и сгруппировать по product_color_id"""
    if not product_color_ids:
        return {}
    result = await db.execute(
        select(ProductSize)
        .where(ProductSize.product_color_id.in_(product_color_ids))
        .order_by(ProductSize.sort_order)
    )
    grouped: dict[int, list[dict]] = defaultdict(list)
    for size in result.scalars().all():
        grouped[size.product_color_id].append({
            "id": size.id,
            "size": size.size,
            "quantity": size.quantity,
            "sort_order": size.sort_order
        })
    return grouped

async def reorder_product_sizes(db: AsyncSession, product_color_id: int, size_ids: List[int]) -> bool:
    """Изменить порядок размеров продукта"""
    result = await db.execute(
        select(ProductSize).where(ProductSize.product_color_id == product_color_id)
    )
    sizes = {s.id: s for s in result.scalars().all()}
    
    for index, size_id in enumerate(size_ids):
        if size_id in sizes:
            sizes[size_id].sort_order = index
            
    await db.commit()
    return True


# --- ProductSection CRUD ---
async def list_product_sections(db: AsyncSession, product_id: int) -> List[ProductSection]:
    """Получить список аккордеонов продукта"""
    result = await db.execute(
        select(ProductSection)
        .where(ProductSection.product_id == product_id)
        .order_by(ProductSection.sort_order)
    )
    return result.scalars().all()

async def create_product_section(db: AsyncSession, product_id: int, section_in: ProductSectionCreate) -> ProductSection:
    """Создать новый аккордеон"""
    db_section = ProductSection(
        product_id=product_id,
        title=section_in.title,
        content=section_in.content,
        sort_order=section_in.sort_order
    )
    db.add(db_section)
    await db.commit()
    await db.refresh(db_section)
    return db_section

async def update_product_section(db: AsyncSession, section_id: int, section_update: ProductSectionUpdate) -> Optional[ProductSection]:
    """Обновить аккордеон"""
    db_section = await db.get(ProductSection, section_id)
    if not db_section:
        return None
    
    update_data = section_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_section, field, value)
    
    await db.commit()
    await db.refresh(db_section)
    return db_section

async def delete_product_section(db: AsyncSession, section_id: int) -> bool:
    """Удалить аккордеон"""
    db_section = await db.get(ProductSection, section_id)
    if not db_section:
        return False
    
    await db.delete(db_section)
    await db.commit()
    return True

async def reorder_product_sections(db: AsyncSession, product_id: int, section_ids: List[int]) -> bool:
    """Изменить порядок аккордеонов продукта"""
    result = await db.execute(
        select(ProductSection).where(ProductSection.product_id == product_id)
    )
    sections = {s.id: s for s in result.scalars().all()}
    
    for index, section_id in enumerate(section_ids):
        if section_id in sections:
            sections[section_id].sort_order = index
            
    await db.commit()
    return True

async def get_sections_for_products(db: AsyncSession, product_ids: List[int]) -> dict[int, list[ProductSection]]:
    """Загрузить аккордеоны для набора продуктов и сгруппировать по product_id"""
    if not product_ids:
        return {}
    result = await db.execute(
        select(ProductSection)
        .where(ProductSection.product_id.in_(product_ids))
        .order_by(ProductSection.sort_order)
    )
    grouped: dict[int, list[ProductSection]] = defaultdict(list)
    for section in result.scalars().all():
        grouped[section.product_id].append(section)
    return grouped
