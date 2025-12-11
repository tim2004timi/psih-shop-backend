from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.category import CategoryCreate
from src.schemas.product import ProductPublic, ProductMeta

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", summary="Дерево категорий")
async def list_categories(db: AsyncSession = Depends(get_db)):
    cats = await crud.get_all_categories(db)
    return crud.build_tree(cats)


@router.get("/{slug}", response_model=List[ProductPublic], summary="Продукты по категории")
async def products_by_category(slug: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from src.models.product import Product
    
    product_colors = await crud.get_products_by_category_slug(db, slug)
    if not product_colors:
        return []
    
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
    
    result: List[ProductPublic] = []
    for pc in product_colors:
        product = products_map.get(pc.product_id)
        if not product:
            continue
        
        result.append(
            ProductPublic(
                id=pc.id,
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
            )
        )
    return result


@router.post("", status_code=201, summary="Создать категорию")
async def create_category(cat: CategoryCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    created = await crud.create_category(db, name=cat.name, slug=cat.slug, parent_id=cat.parent_id, level=cat.level, sort_order=cat.sort_order, is_active=cat.is_active)
    return {"id": created.id, "name": created.name, "slug": created.slug, "parent_id": created.parent_id, "level": created.level, "sort_order": created.sort_order, "is_active": created.is_active}


@router.delete("/{category_id}", status_code=204, summary="Удалить категорию")
async def delete_category(category_id: int, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_category(db, category_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return


