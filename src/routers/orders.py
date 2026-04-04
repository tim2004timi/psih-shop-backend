from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.database import get_db
from src.auth import get_current_user, get_optional_current_user
from src import crud
from src.schemas.orders import (
    OrderCreateRequest,
    OrderDetail,
    OrderCreate,
    OrderProductCreate,
    OrderUpdate
)
from src.cdek import get_cdek_client, CDEKError
from src.services.errors import internal_server_error

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("",
    response_model=OrderDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Создать заказ",
    description="Создает новый заказ с товарами. Автоматически вычисляет total_price и проверяет наличие товаров. Доступно без аутентификации (гостевые заказы).")
async def create_order(
    order_request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    if current_user:
        order_request.order.user_id = current_user["id"]
    
    try:
        order = await crud.create_order(
            db=db,
            order_data=order_request.order,
            products=order_request.products
        )
        
        # Возвращаем полную информацию о заказе
        order_detail = await crud.get_order_detail(db, order.id, include_access_token=True)
        if not order_detail:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created order"
            )
        
        return order_detail
    except HTTPException:
        raise
    except Exception as e:
        raise internal_server_error("Failed to create order")

@router.get("",
    response_model=List[OrderDetail],
    summary="Получить список заказов",
    description="Получает список всех заказов с полной информацией о товарах. Требуется аутентификация.")
async def get_orders(
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(100, ge=1, le=1000, description="Количество записей для возврата"),
    search: Optional[str] = Query(None, description="Search by id, email, phone, status, cdek_status, cdek_number, custom_status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        orders = await crud.get_orders_detail(db, skip=skip, limit=limit, search=search)
        return orders
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get orders: {str(e)}"
        )

@router.get("/{order_id}",
    response_model=OrderDetail,
    summary="Получить заказ по ID",
    description="Получает полную информацию о заказе по его ID, включая список товаров. Требуется аутентификация.")
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Получить заказ по ID"""
    include_access_token = not current_user.get("is_admin", False)
    order = await crud.get_order_detail(db, order_id, include_access_token=include_access_token)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Проверяем, что пользователь может видеть этот заказ
    # Если не админ, то только свои заказы
    if not current_user.get("is_admin", False):
        if order.user_id != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own orders"
            )
    
    return order

@router.put("/{order_id}",
    response_model=OrderDetail,
    summary="Обновить заказ",
    description="Обновляет статус заказа. Доступно только администраторам.")
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Обновить заказ (только статус)"""
    # Проверяем права администратора
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Проверяем, что заказ существует
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Обновляем заказ
    updated_order = await crud.update_order(db, order_id, order_update)
    if not updated_order:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update order"
        )
    
    # Возвращаем полную информацию о заказе
    order_detail = await crud.get_order_detail(db, order_id)
    if not order_detail:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve updated order"
        )
    
    return order_detail


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить заказ",
    description="Удаляет заказ. Доступно только администраторам."
)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    ok = await crud.delete_order(db, order_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    return

@router.post("/test_add_order_to_cdek",
    summary="Тестовый endpoint: добавить заказ в CDEK",
    description="Создает заказ в CDEK и возвращает cdek_uuid. Тестовый endpoint.")
async def test_add_order_to_cdek(
    order_id: int = Query(..., description="ID заказа"),
    shipment_point: str = Query("MSK5", description="Код ПВЗ отправления"),
    delivery_point: str = Query(..., description="Код ПВЗ доставки"),
    tariff_code: int = Query(136, description="Тариф CDEK"),
    forbid_inspection: bool = Query(False, description="Запрет осмотра вложения"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Тестовый endpoint для создания заказа в CDEK"""
    # Проверяем, что заказ существует
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Проверяем права доступа (только свои заказы или админ)
    if not current_user.get("is_admin", False):
        if order.user_id != current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add your own orders to CDEK"
            )
    
    # Получаем CDEK клиент
    cdek_client = get_cdek_client()
    
    try:
        # Создаем заказ в CDEK
        cdek_uuid = await cdek_client.add_order_to_cdek(
            order_id=order_id,
            shipment_point=shipment_point,
            delivery_point=delivery_point,
            db=db,
            tariff_code=tariff_code,
            forbid_inspection=forbid_inspection,
        )
        
        return {"cdek_uuid": cdek_uuid, "message": "Заказ зарегистрирован в СДЭК"}
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CDEK rejected order creation"
        )
    except Exception as e:
        raise internal_server_error("Failed to add order to CDEK")
