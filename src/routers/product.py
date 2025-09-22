from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.product import ProductResponse, ProductCreate, ProductUpdate, ProductList
from src.models.product import ProductStatus

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
    
    return ProductList(
        products=products,
        total=total,
        skip=skip,
        limit=limit
    )

@router.get("/{product_id}", 
    response_model=ProductResponse,
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
    return product

@router.get("/slug/{slug}", 
    response_model=ProductResponse,
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
    return product

@router.post("", 
    response_model=ProductResponse,
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
    return product

@router.put("/{product_id}", 
    response_model=ProductResponse,
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
    
    return product

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
    response_model=ProductResponse,
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
    
    return product

@router.put("/{product_id}/toggle-preorder",
    response_model=ProductResponse,
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
    
    return updated_product
