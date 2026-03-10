from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from typing import List

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.orders import CustomStatusCreate, CustomStatusOut

router = APIRouter(prefix="/custom-statuses", tags=["CustomStatus"])


@router.get("",
    response_model=List[CustomStatusOut],
    summary="Список пользовательских статусов")
async def list_custom_statuses(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return await crud.list_custom_statuses(db)


@router.post("",
    response_model=CustomStatusOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользовательский статус")
async def create_custom_status(
    status_in: CustomStatusCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    exists = await crud.get_custom_status_by_name(db, status_in.name)
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom status already exists")

    try:
        created = await crud.create_custom_status(db, name=status_in.name)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Custom status already exists")

    return created


@router.delete("/{status_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользовательский статус")
async def delete_custom_status(
    status_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    ok = await crud.delete_custom_status(db, status_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Custom status not found")
    return
