from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.collection import CollectionCreate, CollectionUpdate, CollectionResponse, CollectionListResponse, CollectionImageIn, CollectionProductIn
from src.schemas.product import ProductPublic, ProductMeta, ProductColorOut, ProductSizeIn, ProductImageOut
from src.models.product import ProductStatus
from src.utils import upload_image_and_derivatives, build_public_url

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.get("", response_model=CollectionListResponse, summary="Получить список коллекций")
async def get_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех коллекций с изображениями."""
    collections = await crud.get_collections(db, skip=skip, limit=limit)
    total = await crud.get_collections_count(db)
    
    collection_responses = []
    for c in collections:
        images = await crud.get_collection_images(db, c.id)
        collection_responses.append(CollectionResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            season=c.season,
            year=c.year,
            description=c.description,
            story=c.story,
            inspiration=c.inspiration,
            key_pieces=c.key_pieces,
            sustainability=c.sustainability,
            is_new=c.is_new,
            is_featured=c.is_featured,
            category=c.category,
            created_at=c.created_at.isoformat(),
            images=[{"id": img.id, "file": img.file, "sort_order": img.sort_order} for img in images]
        ))
    
    return CollectionListResponse(
        collections=collection_responses,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{collection_id}", response_model=CollectionResponse, summary="Получить коллекцию по ID")
async def get_collection(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить коллекцию по ID с изображениями."""
    collection = await crud.get_collection_by_id(db, collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
    images = await crud.get_collection_images(db, collection_id)
    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        slug=collection.slug,
        season=collection.season,
        year=collection.year,
        description=collection.description,
        story=collection.story,
        inspiration=collection.inspiration,
        key_pieces=collection.key_pieces,
        sustainability=collection.sustainability,
        is_new=collection.is_new,
        is_featured=collection.is_featured,
        category=collection.category,
        created_at=collection.created_at.isoformat(),
        images=[{"id": img.id, "file": img.file, "sort_order": img.sort_order} for img in images]
    )


@router.get("/{collection_id}/products", response_model=List[ProductPublic], summary="Получить продукты коллекции")
async def get_collection_products(
    collection_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить продукты, принадлежащие коллекции."""
    products = await crud.get_products_by_collection(db, collection_id)
    
    ids = [p.id for p in products]
    colors_map = await crud.get_colors_for_products(db, ids)
    sizes_map = await crud.get_sizes_for_products(db, ids)
    images_map = await crud.get_images_for_products(db, ids)

    public_products = []
    for p in products:
        public_products.append(ProductPublic(
            id=p.id,
            slug=p.slug,
            title=p.title,
            categoryPath=[],
            price=p.price,
            discount_price=p.discount_price,
            currency=p.currency,
            colors=colors_map.get(p.id, []),
            sizes=sizes_map.get(p.id, []),
            composition=p.composition,
            fit=p.fit,
            description=p.description,
            images=[{"file": img.file, "alt": None, "w": None, "h": None, "color": None} for img in images_map.get(p.id, [])],
            meta=ProductMeta(care=p.meta_care, shipping=p.meta_shipping, returns=p.meta_returns),
            status=p.status,
        ))
    return public_products


@router.post("", response_model=CollectionResponse, summary="Создать коллекцию", status_code=201)
async def create_collection(
    collection_create: CollectionCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новую коллекцию (только для админов)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Check if collection with this ID already exists
    existing = await crud.get_collection_by_id(db, collection_create.id)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection with this ID already exists")
    
    created_collection = await crud.create_collection(db, collection_create)
    return CollectionResponse(
        id=created_collection.id,
        name=created_collection.name,
        slug=created_collection.slug,
        season=created_collection.season,
        year=created_collection.year,
        description=created_collection.description,
        story=created_collection.story,
        inspiration=created_collection.inspiration,
        key_pieces=created_collection.key_pieces,
        sustainability=created_collection.sustainability,
        is_new=created_collection.is_new,
        is_featured=created_collection.is_featured,
        category=created_collection.category,
        created_at=created_collection.created_at.isoformat(),
        images=[]
    )


@router.put("/{collection_id}", response_model=CollectionResponse, summary="Обновить коллекцию")
async def update_collection(
    collection_id: str,
    collection_update: CollectionUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить коллекцию (только для админов)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    updated_collection = await crud.update_collection(db, collection_id, collection_update)
    if not updated_collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
    images = await crud.get_collection_images(db, collection_id)
    return CollectionResponse(
        id=updated_collection.id,
        name=updated_collection.name,
        slug=updated_collection.slug,
        season=updated_collection.season,
        year=updated_collection.year,
        description=updated_collection.description,
        story=updated_collection.story,
        inspiration=updated_collection.inspiration,
        key_pieces=updated_collection.key_pieces,
        sustainability=updated_collection.sustainability,
        is_new=updated_collection.is_new,
        is_featured=updated_collection.is_featured,
        category=updated_collection.category,
        created_at=updated_collection.created_at.isoformat(),
        images=[{"id": img.id, "file": img.file, "sort_order": img.sort_order} for img in images]
    )


@router.delete("/{collection_id}", summary="Удалить коллекцию", status_code=204)
async def delete_collection(
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить коллекцию (только для админов)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    ok = await crud.delete_collection(db, collection_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    return


@router.post("/{collection_id}/images", summary="Добавить изображение в коллекцию", status_code=201)
async def add_collection_image(
    collection_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить изображение в коллекцию (только для админов)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Check if collection exists
    collection = await crud.get_collection_by_id(db, collection_id)
    if not collection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    
    # Upload image and create derivatives
    image_id = str(uuid.uuid4())
    file_url = await upload_image_and_derivatives(file, file.filename)
    
    # Save to database
    await crud.create_collection_image(db, collection_id, id=image_id, file_url=file_url)
    
    return {"id": image_id, "file": file_url}


@router.delete("/images/{image_id}", summary="Удалить изображение коллекции", status_code=204)
async def delete_collection_image(
    image_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить изображение коллекции (только для админов)."""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    ok = await crud.delete_collection_image(db, image_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return
