from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import logging

from src.cdek import get_cdek_client, CDEKError
from src.schemas.cdek import CDEKCity, CDEKOffice, CDEKOfficeList
from src.database import get_db
from src import crud
from pydantic import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cdek", tags=["CDEK"])


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
    uuid: str
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
    
    try:
        cdek_client = get_cdek_client()
        order_info = await cdek_client.get_order_info_by_uuid(uuid.strip())
        return order_info
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_order_info_by_uuid: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/waybill",
    summary="Получить URL накладной",
    description="Генерирует накладную для заказа в CDEK и возвращает URL для скачивания."
)
async def get_waybill(
    order_id: int = Query(..., description="ID заказа в системе"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Получить URL накладной для заказа
    
    Args:
        order_id: ID заказа в системе
        
    Returns:
        URL для скачивания накладной
        
    Raises:
        HTTPException 404: Если заказ не найден или не зарегистрирован в CDEK
        HTTPException 502: Если произошла ошибка при запросе к CDEK API
    """
    # Получаем заказ из БД
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем наличие cdek_uuid
    if not order.cdek_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не зарегистрирован в СДЭК"
        )
    
    try:
        cdek_client = get_cdek_client()
        url = await cdek_client.generate_waybill_url(order.cdek_uuid)
        return {"url": url}
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_waybill: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/barcode",
    summary="Получить URL штрихкода",
    description="Генерирует штрихкод для заказа в CDEK и возвращает URL для скачивания."
)
async def get_barcode(
    order_id: int = Query(..., description="ID заказа в системе"),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, str]:
    """
    Получить URL штрихкода для заказа
    
    Args:
        order_id: ID заказа в системе
        
    Returns:
        URL для скачивания штрихкода
        
    Raises:
        HTTPException 404: Если заказ не найден или не зарегистрирован в CDEK
        HTTPException 502: Если произошла ошибка при запросе к CDEK API
    """
    # Получаем заказ из БД
    order = await crud.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )
    
    # Проверяем наличие cdek_uuid
    if not order.cdek_uuid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не зарегистрирован в СДЭК"
        )
    
    try:
        cdek_client = get_cdek_client()
        url = await cdek_client.generate_barcode_url(order.cdek_uuid)
        return {"url": url}
        
    except CDEKError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"CDEK API error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_barcode: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

