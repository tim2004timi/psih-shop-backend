from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.models.collection import Collection, CollectionImage, CollectionProduct
from src.models.product import Product
from src.schemas.collection import CollectionCreate, CollectionUpdate


async def get_collections(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Collection]:
    """Получить список коллекций"""
    result = await db.execute(
        select(Collection).offset(skip).limit(limit).order_by(Collection.created_at.desc())
    )
    return result.scalars().all()


async def get_collections_count(db: AsyncSession) -> int:
    """Получить общее количество коллекций"""
    result = await db.execute(select(func.count(Collection.id)))
    return result.scalar()


async def get_collection_by_id(db: AsyncSession, collection_id: str) -> Optional[Collection]:
    """Получить коллекцию по ID"""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    return result.scalar_one_or_none()


async def get_collection_by_slug(db: AsyncSession, slug: str) -> Optional[Collection]:
    """Получить коллекцию по slug"""
    result = await db.execute(select(Collection).where(Collection.slug == slug))
    return result.scalar_one_or_none()


async def create_collection(db: AsyncSession, collection_create: CollectionCreate) -> Collection:
    """Создать новую коллекцию"""
    db_collection = Collection(
        id=collection_create.id,
        name=collection_create.name,
        slug=collection_create.slug,
        season=collection_create.season,
        year=collection_create.year,
        description=collection_create.description,
        story=collection_create.story,
        inspiration=collection_create.inspiration,
        key_pieces=collection_create.key_pieces,
        sustainability=collection_create.sustainability,
        is_new=collection_create.is_new,
        is_featured=collection_create.is_featured,
        category=collection_create.category
    )
    db.add(db_collection)
    await db.commit()
    await db.refresh(db_collection)
    return db_collection


async def update_collection(db: AsyncSession, collection_id: str, update_data: CollectionUpdate) -> Optional[Collection]:
    """Обновить коллекцию"""
    collection = await get_collection_by_id(db, collection_id)
    if not collection:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(collection, field, value)
    
    await db.commit()
    await db.refresh(collection)
    return collection


async def delete_collection(db: AsyncSession, collection_id: str) -> bool:
    """Удалить коллекцию"""
    collection = await get_collection_by_id(db, collection_id)
    if not collection:
        return False
    
    await db.delete(collection)
    await db.commit()
    return True


async def get_collection_images(db: AsyncSession, collection_id: str) -> List[CollectionImage]:
    """Получить изображения коллекции"""
    result = await db.execute(
        select(CollectionImage)
        .where(CollectionImage.collection_id == collection_id)
        .order_by(CollectionImage.sort_order)
    )
    return result.scalars().all()


async def create_collection_image(db: AsyncSession, collection_id: str, *, id: str, file_url: str, sort_order: int = 0) -> CollectionImage:
    """Создать изображение коллекции"""
    img = CollectionImage(id=id, collection_id=collection_id, file=file_url, sort_order=sort_order)
    db.add(img)
    await db.commit()
    await db.refresh(img)
    return img


async def delete_collection_image(db: AsyncSession, image_id: str) -> bool:
    """Удалить изображение коллекции"""
    result = await db.execute(select(CollectionImage).where(CollectionImage.id == image_id))
    img = result.scalar_one_or_none()
    if not img:
        return False
    await db.delete(img)
    await db.commit()
    return True


async def get_products_by_collection(db: AsyncSession, collection_id: str) -> List[Product]:
    """Получить продукты коллекции"""
    result = await db.execute(
        select(Product)
        .join(CollectionProduct, CollectionProduct.product_id == Product.id)
        .where(CollectionProduct.collection_id == collection_id)
        .order_by(CollectionProduct.sort_order)
    )
    return result.scalars().all()


async def add_product_to_collection(db: AsyncSession, collection_id: str, product_id: str, sort_order: int = 0) -> bool:
    """Добавить продукт в коллекцию"""
    # check duplicates
    exists = await db.execute(
        select(CollectionProduct).where(
            CollectionProduct.collection_id == collection_id,
            CollectionProduct.product_id == product_id,
        )
    )
    if exists.scalar_one_or_none():
        return True
    
    link = CollectionProduct(collection_id=collection_id, product_id=product_id, sort_order=sort_order)
    db.add(link)
    await db.commit()
    return True


async def remove_product_from_collection(db: AsyncSession, collection_id: str, product_id: str) -> bool:
    """Удалить продукт из коллекции"""
    result = await db.execute(
        select(CollectionProduct).where(
            CollectionProduct.collection_id == collection_id,
            CollectionProduct.product_id == product_id,
        )
    )
    link = result.scalar_one_or_none()
    if not link:
        return False
    await db.delete(link)
    await db.commit()
    return True
