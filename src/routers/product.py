from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.product import ProductCreate, ProductUpdate, ProductList, ProductPublic, ProductMeta, ProductColorIn, ProductSizeIn
from src.models.product import ProductStatus
import uuid
from src.utils import upload_image_and_derivatives, build_public_url
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
    products = await crud.get_products(db, skip=skip, limit=limit, status=status, search=search)
    total = await crud.get_products_count(db, status=status, search=search)
    ids = [p.id for p in products]
    colors_map = await crud.get_colors_for_products(db, ids)
    sizes_map = await crud.get_sizes_for_products(db, ids)
    
    public_products = []
    for p in products:
        public_products.append(ProductPublic(
            id=p.id,
            slug=p.slug,
            title=p.title,
            categoryPath=[],
            price=p.price,
            currency=p.currency,
            colors=colors_map.get(p.id, []),
            sizes=sizes_map.get(p.id, []),
            composition=p.composition,
            fit=p.fit,
            description=p.description,
            images=[
                {"file": img.file, "alt": None, "w": None, "h": None, "color": None}
                for img in await crud.list_product_images(db, p.id)
            ],
            meta=ProductMeta(care=p.meta_care, shipping=p.meta_shipping, returns=p.meta_returns),
            status=p.status,
        ))

    return ProductList(
        products=public_products,
        total=total,
        skip=skip,
        limit=limit
    )

# --- Categorization management ---
class ProductCategoryIn(BaseModel):
    category_id: str

@router.post("/{product_id}/categories", status_code=204, summary="Добавить продукт в категорию")
async def add_product_category(
    product_id: str,
    body: ProductCategoryIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    await crud.add_product_to_category(db, product_id, body.category_id)
    return

@router.delete("/{product_id}/categories/{category_id}", status_code=204, summary="Удалить продукт из категории")
async def remove_product_category(
    product_id: str,
    category_id: str,
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
    collection_id: str
    sort_order: int = 0

@router.post("/{product_id}/collections", status_code=204, summary="Добавить продукт в коллекцию")
async def add_product_collection(
    product_id: str,
    body: ProductCollectionIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    await crud.add_product_to_collection(db, body.collection_id, product_id, body.sort_order)
    return

@router.delete("/{product_id}/collections/{collection_id}", status_code=204, summary="Удалить продукт из коллекции")
async def remove_product_collection(
    product_id: str,
    collection_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.remove_product_from_collection(db, collection_id, product_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return

# --- Colors management ---
@router.get("/{product_id}/colors", summary="Список цветов продукта")
async def list_colors(product_id: str, db: AsyncSession = Depends(get_db)):
    colors = await crud.list_product_colors(db, product_id)
    return [
        {"id": c.id, "code": c.code, "label": c.label, "hex": c.hex} for c in colors
    ]

@router.post("/{product_id}/colors", summary="Добавить цвет", status_code=201)
async def add_color(
    product_id: str,
    color: ProductColorIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    created = await crud.create_product_color(db, product_id, id=color.id, code=color.code, label=color.label, hex=color.hex)
    return {"id": created.id, "code": created.code, "label": created.label, "hex": created.hex}

@router.delete("/colors/{color_id}", summary="Удалить цвет", status_code=204)
async def delete_color(
    color_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_color(db, color_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Color not found")
    return

# --- Sizes management ---
@router.get("/{product_id}/sizes", summary="Список размеров продукта")
async def list_sizes(product_id: str, db: AsyncSession = Depends(get_db)):
    sizes = await crud.list_product_sizes(db, product_id)
    return [
        {"id": s.id, "size": s.size} for s in sizes
    ]

@router.post("/{product_id}/sizes", summary="Добавить размер", status_code=201)
async def add_size(
    product_id: str,
    size: ProductSizeIn,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    created = await crud.create_product_size(db, product_id, id=size.id, size=size.size)
    return {"id": created.id, "size": created.size}

@router.delete("/sizes/{size_id}", summary="Удалить размер", status_code=204)
async def delete_size(
    size_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_size(db, size_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size not found")
    return

@router.get("/{product_id}", 
    response_model=ProductPublic,
    summary="Получить продукт по ID",
    description="Получает информацию о продукте по его ID")
async def get_product_by_id(
    product_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить продукт по ID"""
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    colors_map = await crud.get_colors_for_products(db, [product.id])
    sizes_map = await crud.get_sizes_for_products(db, [product.id])
    images = await crud.list_product_images(db, product.id)
    return ProductPublic(
        id=product.id,
        slug=product.slug,
        title=product.title,
        categoryPath=[],
        price=product.price,
        currency=product.currency,
        colors=colors_map.get(product.id, []),
        sizes=sizes_map.get(product.id, []),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
        meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
        status=product.status,
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
    product = await crud.get_product_by_slug(db, slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    colors_map = await crud.get_colors_for_products(db, [product.id])
    sizes_map = await crud.get_sizes_for_products(db, [product.id])
    images = await crud.list_product_images(db, product.id)
    return ProductPublic(
        id=product.id,
        slug=product.slug,
        title=product.title,
        categoryPath=[],
        price=product.price,
        currency=product.currency,
        colors=colors_map.get(product.id, []),
        sizes=sizes_map.get(product.id, []),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
        meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
        status=product.status,
    )

@router.post("", 
    response_model=ProductPublic,
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
    
    # Проверяем, существует ли продукт с таким ID
    existing_product = await crud.get_product_by_id(db, product_create.id)
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this ID already exists"
        )
    
    # Проверяем, существует ли slug
    if await crud.check_slug_exists(db, product_create.slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this slug already exists"
        )
    
    product = await crud.create_product(db, product_create)
    images = await crud.list_product_images(db, product.id)
    return ProductPublic(
        id=product.id,
        slug=product.slug,
        title=product.title,
        categoryPath=[],
        price=product.price,
        currency=product.currency,
        colors=[],
        sizes=[],
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
        meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
        status=product.status,
    )

@router.put("/{product_id}", 
    response_model=ProductPublic,
    summary="Обновить продукт",
    description="Обновляет информацию о продукте (только для админов)")
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить продукт"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Проверяем slug, если он обновляется
    if product_update.slug:
        if await crud.check_slug_exists(db, product_update.slug, exclude_id=product_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product with this slug already exists"
            )
    
    product = await crud.update_product(db, product_id, product_update)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    colors_map = await crud.get_colors_for_products(db, [product.id])
    sizes_map = await crud.get_sizes_for_products(db, [product.id])
    images = await crud.list_product_images(db, product.id)
    return ProductPublic(
        id=product.id,
        slug=product.slug,
        title=product.title,
        categoryPath=[],
        price=product.price,
        currency=product.currency,
        colors=colors_map.get(product.id, []),
        sizes=sizes_map.get(product.id, []),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],)

@router.get("/{product_id}/images", summary="Список изображений продукта")
async def list_images(product_id: str, db: AsyncSession = Depends(get_db)):
    images = await crud.list_product_images(db, product_id)
    return [
        {"id": i.id, "file": i.file, "sort_order": i.sort_order} for i in images
    ]

@router.post("/{product_id}/images", summary="Загрузить изображение", status_code=201)
async def upload_image(
    product_id: str,
    sort_order: int = 0,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    file_url = await upload_image_and_derivatives(file, file.filename)
    # medium/small остаются только в хранилище
    img_id = str(uuid.uuid4())
    created = await crud.create_product_image(db, product_id, id=img_id, file_url=file_url, sort_order=sort_order)
    return {"id": created.id, "file": created.file, "sort_order": created.sort_order}

@router.delete("/images/{image_id}", summary="Удалить изображение", status_code=204)
async def delete_image(
    image_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_product_image(db, image_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return

@router.delete("/{product_id}",
    summary="Удалить продукт",
    description="Удаляет продукт (только для админов)")
async def delete_product(
    product_id: str,
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

@router.put("/{product_id}/status",
    response_model=ProductPublic,
    summary="Изменить статус продукта",
    description="Изменяет статус продукта (только для админов)")
async def update_product_status(
    product_id: str,
    new_status: ProductStatus,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Изменить статус продукта"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    product = await crud.update_product(db, product_id, ProductUpdate(status=new_status))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    colors_map = await crud.get_colors_for_products(db, [product.id])
    sizes_map = await crud.get_sizes_for_products(db, [product.id])
    return ProductPublic(
        id=product.id,
        slug=product.slug,
        title=product.title,
        categoryPath=[],
        price=product.price,
        currency=product.currency,
        colors=colors_map.get(product.id, []),
        sizes=sizes_map.get(product.id, []),
        composition=product.composition,
        fit=product.fit,
        description=product.description,
        images=[],
        meta=ProductMeta(care=product.meta_care, shipping=product.meta_shipping, returns=product.meta_returns),
        status=product.status,
    )

@router.put("/{product_id}/toggle-preorder",
    response_model=ProductPublic,
    summary="Переключить предзаказ",
    description="Переключает возможность предзаказа для продукта (только для админов)")
async def toggle_preorder(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Переключить возможность предзаказа"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    product = await crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Переключаем статус предзаказа
    new_preorder_status = not product.is_pre_order
    updated_product = await crud.update_product(
        db, 
        product_id, 
        ProductUpdate(is_pre_order=new_preorder_status)
    )
    
    colors_map = await crud.get_colors_for_products(db, [updated_product.id])
    sizes_map = await crud.get_sizes_for_products(db, [updated_product.id])
    return ProductPublic(
        id=updated_product.id,
        slug=updated_product.slug,
        title=updated_product.title,
        categoryPath=[],
        price=updated_product.price,
        currency=updated_product.currency,
        colors=colors_map.get(updated_product.id, []),
        sizes=sizes_map.get(updated_product.id, []),
        composition=updated_product.composition,
        fit=updated_product.fit,
        description=updated_product.description,
        images=[],
        meta=ProductMeta(care=updated_product.meta_care, shipping=updated_product.meta_shipping, returns=updated_product.meta_returns),
        status=updated_product.status,
    )
