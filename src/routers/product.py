from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy import select

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.product import (
    ProductCreate, ProductUpdate, ProductList, ProductPublic, ProductMeta,
    ProductColorIn, ProductSizeIn, ProductColorUpdate, ProductDetail, ProductColorDetail
)
from src.models.product import ProductStatus, Product, ProductColor
from src.utils import upload_image_and_derivatives
from pydantic import BaseModel

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", 
    response_model=ProductList,
    summary="Получить список продуктов",
    description="Получает список всех продуктов с пагинацией и фильтрацией")
async def get_products(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей для возврата"),
    status: Optional[ProductStatus] = Query(None, description="Фильтр по статусу продукта"),
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список продуктов с фильтрацией"""
    product_colors = await crud.get_products(db, skip=skip, limit=limit, status=status, search=search)
    total = await crud.get_products_count(db, status=status, search=search)
    
    # Получаем связанные продукты
    product_ids = list(set([pc.product_id for pc in product_colors]))
    products_map = {}
    if product_ids:
        result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        for p in result.scalars().all():
            products_map[p.id] = p
    
    # Получаем размеры и изображения
    color_ids = [pc.id for pc in product_colors]
    sizes_map = await crud.get_sizes_for_products(db, color_ids)
    images_map = await crud.get_images_for_products(db, color_ids)
    
    public_products = []
    for pc in product_colors:
        product = products_map.get(pc.product_id)
        if not product:
            continue
            
        public_products.append(ProductPublic(
            id=product.id,
            color_id=pc.id,
            slug=pc.slug,
            title=pc.title,
            categoryPath=[],
            price=product.price,
            discount_price=product.discount_price,
            currency=product.currency,
            label=pc.label,
            hex=pc.hex,
            sizes=sizes_map.get(pc.id, []),
            composition=product.composition,
            fit=product.fit,
            description=product.description,
            images=[{"file": img.file, "alt": None, "w": None, "h": None, "color": None} for img in images_map.get(pc.id, [])],
            meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
            status=product.status,
        ))

    return ProductList(
        products=public_products,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/slug/{slug}", 
    response_model=ProductPublic,
    summary="Получить продукт по slug",
    description="Получает информацию о продукте по его slug")
async def get_product_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить продукт по slug"""
    product_color = await crud.get_product_by_slug(db, slug)
    if not product_color:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product = await crud.get_product_by_id(db, product_color.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    sizes_map = await crud.get_sizes_for_products(db, [product_color.id])
    images = await crud.list_product_images(db, product_color.id)
    main_category = await crud.get_product_main_category(db, product.id)
    
    return ProductPublic(
        id=product.id,
        color_id=product_color.id,
        slug=product_color.slug,
        title=product_color.title,
        categoryPath=[],
        main_category=main_category,
        price=product.price,
        discount_price=product.discount_price,
        currency=product.currency,
        label=product_color.label,
        hex=product_color.hex,
        sizes=sizes_map.get(product_color.id, []),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
        meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
        status=product.status,
    )

# --- Product management ---
@router.post("", 
    response_model=dict,
    summary="Создать новый продукт",
    description="Создает новый продукт (только для админов)")
async def create_product(
    product_create: ProductCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать новый продукт"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    product = await crud.create_product(db, product_create)
    return {"id": product.id, "message": "Product created. Now create a color variant."}

@router.put("/base/{product_id}", 
    response_model=dict,
    summary="Обновить базовый продукт",
    description="Обновляет информацию о базовом продукте (только для админов)")
async def update_product(
    product_id: int,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить базовый продукт"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    product = await crud.update_product(db, product_id, product_update)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"id": product.id, "message": "Product updated"}

@router.delete("/base/{product_id}",
    summary="Удалить продукт",
    description="Удаляет продукт (только для админов)")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить продукт"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    success = await crud.delete_product(db, product_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {"message": "Product deleted successfully"}

# --- ProductColor management ---
@router.get("/{product_id}/colors", summary="Список цветов продукта")
async def list_colors(product_id: int, db: AsyncSession = Depends(get_db)):
    colors = await crud.list_product_colors(db, product_id)
    return [
        {"id": c.id, "slug": c.slug, "title": c.title, "label": c.label, "hex": c.hex} for c in colors
    ]

@router.post("/{product_id}/colors", summary="Добавить цвет", status_code=201)
async def add_color(
    product_id: int,
    color: ProductColorIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Проверяем slug
    if await crud.check_slug_exists(db, color.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this slug already exists"
        )
    
    created = await crud.create_product_color(
        db, product_id, 
        slug=color.slug, 
        title=color.title, 
        label=color.label, 
        hex=color.hex
    )
    return {"id": created.id, "slug": created.slug, "title": created.title, "label": created.label, "hex": created.hex}

@router.put("/colors/{color_id}", summary="Обновить цвет", status_code=200)
async def update_color(
    color_id: int,
    color_update: ProductColorUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    # Проверяем slug, если он обновляется
    if color_update.slug:
        if await crud.check_slug_exists(db, color_update.slug, exclude_id=color_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this slug already exists"
            )
    
    updated = await crud.update_product_color(db, color_id, color_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
    return {"id": updated.id, "slug": updated.slug, "title": updated.title, "label": updated.label, "hex": updated.hex}

@router.delete("/colors/{color_id}", summary="Удалить цвет", status_code=204)
async def delete_color(
    color_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_color(db, color_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
    return

# --- ProductImage management ---
@router.get("/colors/{product_color_id}/images", summary="Список изображений продукта")
async def list_images(product_color_id: int, db: AsyncSession = Depends(get_db)):
    images = await crud.list_product_images(db, product_color_id)
    return [
        {"id": i.id, "file": i.file, "sort_order": i.sort_order} for i in images
    ]

@router.post("/colors/{product_color_id}/images", summary="Загрузить изображение", status_code=201)
async def upload_image(
    product_color_id: int,
    sort_order: int = 0,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    file_url = await upload_image_and_derivatives(file, file.filename)
    created = await crud.create_product_image(db, product_color_id, file_url=file_url, sort_order=sort_order)
    return {"id": created.id, "file": created.file, "sort_order": created.sort_order}

@router.post("/colors/{product_color_id}/primary-image", summary="Загрузить главное изображение", status_code=201)
async def upload_primary_image(
    product_color_id: int,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    
    color = await crud.get_product_color_by_id(db, product_color_id)
    if not color:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product color not found")
    
    await crud.delete_primary_image(db, product_color_id)
    
    file_url = await upload_image_and_derivatives(file, file.filename)
    created = await crud.create_product_image(db, product_color_id, file_url=file_url, sort_order=1000)
    return {"id": created.id, "file": created.file, "sort_order": created.sort_order}

@router.delete("/images/{image_id}", summary="Удалить изображение", status_code=204)
async def delete_image(
    image_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_image(db, image_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return

# --- ProductSize management ---
@router.get("/colors/{product_color_id}/sizes", summary="Список размеров продукта")
async def list_sizes(product_color_id: int, db: AsyncSession = Depends(get_db)):
    sizes = await crud.list_product_sizes(db, product_color_id)
    return [
        {"id": s.id, "size": s.size, "quantity": s.quantity} for s in sizes
    ]

@router.post("/colors/{product_color_id}/sizes", summary="Добавить размер", status_code=201)
async def add_size(
    product_color_id: int,
    size: ProductSizeIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    created = await crud.create_product_size(db, product_color_id, size=size.size, quantity=size.quantity)
    return {"id": created.id, "size": created.size, "quantity": created.quantity}

@router.put("/sizes/{size_id}", summary="Обновить размер", status_code=200)
async def update_size(
    size_id: int,
    size: Optional[str] = None,
    quantity: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    updated = await crud.update_product_size(db, size_id, size=size, quantity=quantity)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
    return {"id": updated.id, "size": updated.size, "quantity": updated.quantity}

@router.delete("/sizes/{size_id}", summary="Удалить размер", status_code=204)
async def delete_size(
    size_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_size(db, size_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
    return

# --- Categorization management ---
class ProductCategoryIn(BaseModel):
    category_id: int

@router.post("/base/{product_id}/categories", status_code=204, summary="Добавить продукт в категорию")
async def add_product_category(
    product_id: int,
    body: ProductCategoryIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    await crud.add_product_to_category(db, product_id, body.category_id)
    return

@router.delete("/base/{product_id}/categories/{category_id}", status_code=204, summary="Удалить продукт из категории")
async def remove_product_category(
    product_id: int,
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.remove_product_from_category(db, product_id, category_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return

# --- Collection management ---
class ProductCollectionIn(BaseModel):
    collection_id: int
    sort_order: int = 0

@router.post("/base/{product_id}/collections", status_code=204, summary="Добавить продукт в коллекцию")
async def add_product_collection(
    product_id: int,
    body: ProductCollectionIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    await crud.add_product_to_collection(db, body.collection_id, product_id, body.sort_order)
    return

@router.delete("/base/{product_id}/collections/{collection_id}", status_code=204, summary="Удалить продукт из коллекции")
async def remove_product_collection(
    product_id: int,
    collection_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.remove_product_from_collection(db, collection_id, product_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return

@router.get("/{product_id}", 
    response_model=ProductDetail,
    summary="Получить продукт по ID",
    description="Получает детальную информацию о продукте по его ID со всеми цветами, изображениями и размерами")
async def get_product_by_id(
    product_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить продукт по ID со всеми цветами"""
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Получаем все цвета продукта
    colors = await crud.list_product_colors(db, product_id)
    main_category = await crud.get_product_main_category(db, product_id)

    if not colors:
        # Если нет цветов, возвращаем продукт с пустым списком цветов
        return ProductDetail(
            id=product.id,
            description=product.description,
            price=product.price,
            discount_price=product.discount_price,
            currency=product.currency,
            composition=product.composition,
            fit=product.fit,
            status=product.status,
            is_pre_order=product.is_pre_order,
            main_category=main_category,
            meta_care=product.meta_care,
            meta_shipping=product.meta_shipping,
            meta_returns=product.meta_returns,
            colors=[]
        )
    
    # Получаем все ID цветов для загрузки изображений и размеров
    color_ids = [color.id for color in colors]
    
    # Загружаем изображения и размеры для всех цветов
    images_map = await crud.get_images_for_products(db, color_ids)
    sizes_map = await crud.get_sizes_for_products(db, color_ids)
    
    # Формируем список цветов с изображениями и размерами
    colors_detail = []
    for color in colors:
        images = images_map.get(color.id, [])
        sizes = sizes_map.get(color.id, [])
        
        colors_detail.append(ProductColorDetail(
            color_id=color.id,
            slug=color.slug,
            title=color.title,
            label=color.label,
            hex=color.hex,
            images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
            sizes=sizes
        ))
    
    return ProductDetail(
        id=product.id,
        description=product.description,
        price=product.price,
        discount_price=product.discount_price,
        currency=product.currency,
        composition=product.composition,
        fit=product.fit,
        status=product.status,
        is_pre_order=product.is_pre_order,
        main_category=main_category,
        meta_care=product.meta_care,
        meta_shipping=product.meta_shipping,
        meta_returns=product.meta_returns,
        colors=colors_detail
    )
