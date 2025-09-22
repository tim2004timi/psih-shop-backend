from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.auth import get_current_user
from src import crud
from src.schemas.user import UserResponse, UserUpdate, UserCreate
from src.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.put("/me", 
    response_model=UserResponse,
    summary="Обновить информацию о текущем пользователе",
    description="Обновляет информацию о текущем аутентифицированном пользователе")
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить информацию текущего пользователя"""
    user = await crud.get_user_by_id(db, current_user["id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Обновляем только переданные поля
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/{user_id}", 
    response_model=UserResponse,
    summary="Получить пользователя по ID",
    description="Получает информацию о пользователе по ID (только для админов или самого пользователя)")
async def get_user_by_id(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить пользователя по ID (только для админов или себя)"""
    if user_id != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.get("", 
    response_model=List[UserResponse],
    summary="Получить список пользователей",
    description="Получает список всех пользователей с пагинацией (только для админов)")
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить список пользователей (только для админов)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Здесь нужно реализовать пагинацию в crud
    users = await crud.get_users(db, skip=skip, limit=limit)
    return users

@router.put("/{user_id}/activate", 
    response_model=UserResponse,
    summary="Активировать пользователя",
    description="Активирует пользователя по ID (только для админов)")
async def activate_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Активировать пользователя (только для админов)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/{user_id}/deactivate", 
    response_model=UserResponse,
    summary="Деактивировать пользователя",
    description="Деактивирует пользователя по ID (только для админов)")
async def deactivate_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Деактивировать пользователя (только для админов)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}",
    summary="Удалить пользователя",
    description="Удаляет пользователя по ID (только для админов)")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить пользователя (только для админов)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}

@router.put("/{user_id}/verify-email", 
    response_model=UserResponse,
    summary="Подтвердить email пользователя",
    description="Подтверждает email пользователя по ID (только для админов или самого пользователя)")
async def verify_user_email(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Подтвердить email пользователя (только для админов или себя)"""
    if user_id != current_user["id"] and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.email_verified = True
    await db.commit()
    await db.refresh(user)
    return user

@router.get("/search/{email}", 
    response_model=Optional[UserResponse],
    summary="Поиск пользователя по email",
    description="Ищет пользователя по email адресу (только для админов)")
async def search_user_by_email(
    email: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Поиск пользователя по email (только для админов)"""
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    user = await crud.get_user_by_email(db, email)
    return user