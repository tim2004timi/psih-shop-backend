from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from decimal import Decimal

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.promocode import (
    PromoCodeCreate,
    PromoCodeUpdate,
    PromoCodeResponse,
    PromoCodeValidateRequest,
    PromoCodeValidateResponse,
)

router = APIRouter(prefix="/promocodes", tags=["PromoCodes"])


@router.post(
    "",
    response_model=PromoCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать промокод",
)
async def create_promo(
    data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    existing = await crud.get_promo_code_by_code(db, data.code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Промокод с таким кодом уже существует")

    promo = await crud.create_promo_code(db, data)
    return promo


@router.get(
    "",
    response_model=List[PromoCodeResponse],
    summary="Получить список промокодов",
)
async def list_promos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return await crud.get_promo_codes(db, skip=skip, limit=limit)


@router.put(
    "/{promo_id}",
    response_model=PromoCodeResponse,
    summary="Обновить промокод",
)
async def update_promo(
    promo_id: int,
    data: PromoCodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    promo = await crud.update_promo_code(db, promo_id, data)
    if not promo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден")
    return promo


@router.delete(
    "/{promo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить промокод",
)
async def delete_promo(
    promo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    deleted = await crud.delete_promo_code(db, promo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Промокод не найден")


@router.post(
    "/validate",
    response_model=PromoCodeValidateResponse,
    summary="Проверить промокод",
)
async def validate_promo(
    data: PromoCodeValidateRequest,
    db: AsyncSession = Depends(get_db),
):
    return await crud.validate_promo_code(db, data.code, data.order_amount)
