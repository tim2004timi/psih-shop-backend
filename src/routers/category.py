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
    products = await crud.get_products_by_category_slug(db, slug)
    ids = [p.id for p in products]
    colors_map = await crud.get_colors_for_products(db, ids)
    sizes_map = await crud.get_sizes_for_products(db, ids)
    result: List[ProductPublic] = []
    for p in products:
        images = await crud.list_product_images(db, p.id)
        result.append(
            ProductPublic(
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
                images=[{"file": i.file, "alt": None, "w": None, "h": None, "color": None} for i in images],
                meta=ProductMeta(care=p.meta_care, shipping=p.meta_shipping, returns=p.meta_returns),
                status=p.status,
            )
        )
    return result


@router.post("", status_code=201, summary="Создать категорию")
async def create_category(cat: CategoryCreate, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    created = await crud.create_category(db, id=cat.id, name=cat.name, slug=cat.slug, parent_id=cat.parent_id, level=cat.level, sort_order=cat.sort_order, is_active=cat.is_active)
    return {"id": created.id, "name": created.name, "slug": created.slug, "parent_id": created.parent_id, "level": created.level, "sort_order": created.sort_order, "is_active": created.is_active}


@router.delete("/{category_id}", status_code=204, summary="Удалить категорию")
async def delete_category(category_id: str, current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_category(db, category_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return


