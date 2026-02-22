from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
import logging
import httpx

from sqlalchemy import select
from src.cdek import get_cdek_client, CDEKError
from src.schemas.cdek import CDEKCity, CDEKOffice, CDEKOfficeList, CDEKOrderUpdate
from src.database import get_db
from src.config import settings
from src.auth import get_current_user
from src.models.orders import Order
from src import crud
from src.models.orders import Order
from pydantic import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cdek", tags=["CDEK"])


def _build_webhook_url(path: str) -> str:
    url = "http://" + settings.HOST.strip() + ":8000/api/" + path
    return url


@router.get(
    "/suggest_cities",
    response_model=List[CDEKCity],
    summary="Получить список городов по названию",
    description="Получает список городов из CDEK API по названию. Результаты кешируются на 1 день."
)
async def suggest_cities(
    name: str = Query(..., min_length=1, description="Название города для поиска")
) -> List[CDEKCity]:
    """
    Получить список городов по названию из CDEK API
    
    Args:
        name: Название города для поиска (минимум 1 символ)
        
    Returns:
        Список городов с информацией: city_uuid, code, full_name, country_code
        
    Raises:
        HTTPException: Если произошла ошибка при запросе к CDEK API
    """
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="City name cannot be empty"
        )
    
    try:
        cdek_client = get_cdek_client()
        cities_data = await cdek_client.get_suggest_cities(name.strip())
        
        # Преобразуем данные из CDEK API в схему Pydantic
        cities = []
        for city_data in cities_data:
            try:
                # Валидируем данные через Pydantic
                city = CDEKCity(**city_data)
                cities.append(city)
            except ValidationError as e:
                # Пропускаем некорректные записи, но логируем
                logger.warning(f"Skipping invalid city data: {city_data}, validation errors: {e.errors()}")
                continue
            except Exception as e:
                logger.warning(f"Skipping invalid city data: {city_data}, error: {e}")
                continue
        
        return cities
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in suggest_cities: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/offices",
    response_model=List[CDEKOffice],
    summary="Получить список пунктов выдачи по коду города",
    description="Получает список пунктов выдачи (офисов) из CDEK API по коду города. Результаты кешируются на 1 день."
)
async def get_offices(
    city_code: int = Query(..., description="Код города в системе CDEK"),
    office_type: str = Query("PVZ", description="Тип пункта выдачи (по умолчанию PVZ)")
) -> List[CDEKOffice]:
    """
    Получить список пунктов выдачи по коду города из CDEK API
    
    Args:
        city_code: Код города в системе CDEK
        office_type: Тип пункта выдачи (по умолчанию "PVZ" - пункт выдачи заказов)
        
    Returns:
        Список пунктов выдачи с информацией: code, uuid, work_time, city_code, city, longitude, latitude, address
        
    Raises:
        HTTPException: Если произошла ошибка при запросе к CDEK API
    """
    try:
        cdek_client = get_cdek_client()
        offices_data = await cdek_client.get_offices_by_city_code(city_code, office_type)
        
        # Преобразуем данные из CDEK API в схему Pydantic
        offices = []
        for office_data in offices_data:
            try:
                # Извлекаем данные из вложенного объекта location
                location = office_data.get("location", {})
                
                # Формируем объект офиса с нужными полями
                office = CDEKOffice(
                    code=office_data.get("code", ""),
                    uuid=office_data.get("uuid", ""),
                    type=office_data.get("type", "PVZ"),
                    work_time=office_data.get("work_time"),
                    city_code=location.get("city_code", 0),
                    city=location.get("city", ""),
                    longitude=location.get("longitude", 0.0),
                    latitude=location.get("latitude", 0.0),
                    address=location.get("address", "")
                )
                offices.append(office)
            except ValidationError as e:
                # Пропускаем некорректные записи, но логируем
                logger.warning(f"Skipping invalid office data: {office_data}, validation errors: {e.errors()}")
                continue
            except Exception as e:
                logger.warning(f"Skipping invalid office data: {office_data}, error: {e}")
                continue
        
        return offices
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_offices: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/order/{uuid}",
    summary="Получить информацию о заказе по UUID",
    description="Получает информацию о заказе в CDEK по его UUID."
)
async def get_order_info_by_uuid(
    uuid: str,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Получить информацию о заказе в CDEK по UUID
    
    Args:
        uuid: UUID заказа в системе CDEK
        
    Returns:
        JSON ответ с информацией о заказе
        
    Raises:
        HTTPException: Если произошла ошибка при запросе к CDEK API
    """
    if not uuid or not uuid.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID cannot be empty"
        )
    
    # Get order from DB first
    result = await db.execute(
        select(Order).where(Order.cdek_uuid == uuid.strip())
    )
    db_order = result.scalar_one_or_none()

    try:
        cdek_client = get_cdek_client()
        order_info = await cdek_client.get_order_info_by_uuid(uuid.strip())
        
        cdek_number = order_info.get("cdek_number") or order_info.get("entity", {}).get("cdek_number")
        if cdek_number and db_order and not db_order.cdek_number:
            db_order.cdek_number = str(cdek_number)
            await db.commit()
        
        return order_info
        
    except (CDEKError, Exception) as e:
        logger.error(f"CDEK API error for uuid {uuid}: {str(e)}")
        # Fallback: return what we have in DB
        if db_order:
            return {
                "cdek_number": db_order.cdek_number,
                "uuid": db_order.cdek_uuid,
                "status": None,
            }
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )


async def _proxy_cdek_pdf(url: str, filename: str) -> StreamingResponse:
    """Download PDF from CDEK (with auth) and proxy it to the client."""
    cdek_client = get_cdek_client()
    token = await cdek_client._get_access_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to download PDF from CDEK: {resp.status_code} - {resp.text}"
            )
        return StreamingResponse(
            iter([resp.content]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )


@router.patch(
    "/order/{uuid}",
    summary="Обновить заказ в CDEK (type=1)",
    description="Обновляет заказ в CDEK. Использует PATCH /v2/orders."
)
async def update_cdek_order(
    uuid: str,
    payload: CDEKOrderUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    if not uuid or not uuid.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID cannot be empty"
        )
    
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cdek_client = get_cdek_client()
        body = payload.dict(exclude_none=True)
        body["uuid"] = uuid.strip()
        result = await cdek_client.update_order(body)
        
        # Update local order after successful CDEK update
        order: Order | None = None
        if payload.number:
            try:
                order_id = int(str(payload.number))
                order_result = await db.execute(select(Order).where(Order.id == order_id))
                order = order_result.scalar_one_or_none()
            except Exception:
                order = None
        
        if not order:
            order_result = await db.execute(select(Order).where(Order.cdek_uuid == uuid.strip()))
            order = order_result.scalar_one_or_none()
        
        if order:
            # Update recipient info if provided
            if payload.recipient:
                recipient = payload.recipient
                name = recipient.get("name")
                if isinstance(name, str) and name.strip():
                    parts = name.strip().split()
                    order.first_name = parts[0]
                    if len(parts) > 1:
                        order.last_name = " ".join(parts[1:])
                phone_list = recipient.get("phones") or []
                if isinstance(phone_list, list) and phone_list:
                    phone_number = phone_list[0].get("number") if isinstance(phone_list[0], dict) else None
                    if phone_number:
                        order.phone = phone_number
                email = recipient.get("email")
                if isinstance(email, str) and email.strip():
                    order.email = email.strip()
            
            await db.commit()
        
        return result
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CDEK error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_cdek_order: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/waybill",
    summary="Скачать накладную",
    description="Генерирует накладную для заказа в CDEK и возвращает PDF."
)
async def get_waybill(
    order_id: int = Query(..., description="ID заказа в системе"),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    if not order.cdek_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не зарегистрирован в СДЭК")
    
    try:
        cdek_client = get_cdek_client()
        url = await cdek_client.generate_waybill_url(order.cdek_uuid)
        return await _proxy_cdek_pdf(url, f"waybill_{order_id}.pdf")
    except CDEKError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"CDEK API error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_waybill: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.get(
    "/barcode",
    summary="Скачать штрихкод",
    description="Генерирует штрихкод для заказа в CDEK и возвращает PDF."
)
async def get_barcode(
    order_id: int = Query(..., description="ID заказа в системе"),
    db: AsyncSession = Depends(get_db)
):
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    if not order.cdek_uuid:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заказ не зарегистрирован в СДЭК")
    
    try:
        cdek_client = get_cdek_client()
        url = await cdek_client.generate_barcode_url(order.cdek_uuid)
        return await _proxy_cdek_pdf(url, f"barcode_{order_id}.pdf")
    except CDEKError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"CDEK API error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_barcode: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


@router.post(
    "/subscribe_order_status",
    summary="Подписать CDEK на вебхук статусов заказа",
    description="Создает подписку CDEK на тип ORDER_STATUS и URL webhook/order_status."
)
async def subscribe_order_status_webhook(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    webhook_url = _build_webhook_url("webhook/order_status")
    try:
        cdek_client = get_cdek_client()
        return await cdek_client.create_webhook("ORDER_STATUS", webhook_url)
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CDEK error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in subscribe_order_status_webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete(
    "/unsubscribe_order_status/{uuid}",
    summary="Удалить подписку на вебхук по UUID",
    description="Удаляет подписку CDEK на вебхуки по UUID."
)
async def delete_webhook(
    uuid: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    if not uuid or not uuid.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UUID cannot be empty"
        )
    
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    try:
        cdek_client = get_cdek_client()
        return await cdek_client.delete_webhook(uuid.strip())
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CDEK error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in delete_webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
