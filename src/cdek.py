import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from cachetools import TTLCache
from src.config import settings

logger = logging.getLogger(__name__)


class CDEKError(Exception):
    """Исключение для ошибок CDEK API"""
    pass


class CDEKClient:
    """Клиент для работы с CDEK API"""
    
    def __init__(
        self,
        account: Optional[str] = None,
        secure_password: Optional[str] = None,
        api_url: Optional[str] = None,
        test_mode: Optional[bool] = None
    ):
        self.account = account or settings.CDEK_ACCOUNT
        self.secure_password = secure_password or settings.CDEK_SECURE_PASSWORD
        self.test_mode = test_mode if test_mode is not None else settings.CDEK_TEST_MODE
        
        # Определяем URL API
        if api_url:
            self.api_url = api_url
        elif self.test_mode:
            self.api_url = "https://api.edu.cdek.ru/v2"
        else:
            self.api_url = settings.CDEK_API_URL or "https://api.cdek.ru/v2"
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # Кеш для городов с TTL 1 день (86400 секунд)
        # TTLCache автоматически удаляет истекшие записи
        self._cities_cache: TTLCache[str, List[Dict[str, Any]]] = TTLCache(
            maxsize=1000,  # Максимум 1000 городов в кеше
            ttl=86400  # 1 день в секундах
        )
        
        # Кеш для офисов (пунктов выдачи) с TTL 1 день
        self._offices_cache: TTLCache[str, List[Dict[str, Any]]] = TTLCache(
            maxsize=1000,  # Максимум 1000 записей в кеше
            ttl=86400  # 1 день в секундах
        )
        
        if not self.account or not self.secure_password:
            logger.warning(
                "CDEK credentials not set. CDEK integration will not work. "
                "Set CDEK_ACCOUNT and CDEK_SECURE_PASSWORD in environment variables."
            )
    
    async def _get_access_token(self) -> str:
        # Проверяем, не истек ли текущий токен (с запасом 5 минут)
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        if not self.account or not self.secure_password:
            raise CDEKError("CDEK credentials not configured")
        
        # Получаем новый токен
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://api.cdek.ru/v2/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.account,
                        "client_secret": self.secure_password
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK token request failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to get CDEK access token: {response.status_code}")
                
                data = response.json()
                
                if "access_token" not in data:
                    logger.error(f"CDEK token response missing access_token: {data}")
                    raise CDEKError("Invalid response from CDEK token endpoint")
                
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("CDEK access token obtained successfully")
                return self._access_token
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while getting CDEK token: {str(e)}")
                raise CDEKError(f"CDEK authentication failed: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error while getting CDEK token: {str(e)}")
                raise CDEKError(f"CDEK authentication failed: {str(e)}")
    
    async def add_order_to_cdek(
        self,
        order_id: int,
        shipment_point: str,
        delivery_point: str,
        db: "AsyncSession"
    ) -> str:
        """
        Создать заказ в CDEK и сохранить UUID в БД
        
        Args:
            order_id: ID заказа в системе
            shipment_point: Код ПВЗ отправления (например, "MSK5")
            delivery_point: Код ПВЗ доставки (например, "MSK71")
            db: Сессия БД для получения данных заказа и обновления cdek_uuid
            
        Returns:
            UUID заказа в системе CDEK
            
        Raises:
            CDEKError: Если не удалось создать заказ в CDEK или заказ не найден
        """
        # Получаем детальную информацию о заказе из БД
        from src.crud.orders import get_order_detail
        
        order_detail = await get_order_detail(db, order_id)
        if not order_detail:
            raise CDEKError(f"Order {order_id} not found")
        
        # Преобразуем order_detail в dict
        if hasattr(order_detail, "dict"):
            order_detail_dict = order_detail.dict()
        elif hasattr(order_detail, "model_dump"):
            order_detail_dict = order_detail.model_dump()
        else:
            order_detail_dict = order_detail
        
        # Получаем токен
        token = await self._get_access_token()
        
        # Подготавливаем товары для CDEK
        items = []
        total_weight = 0
        
        # Получаем список товаров
        products_list = order_detail_dict.get("products", [])
        
        if not products_list:
            raise CDEKError(f"Order {order_id} has no products")
        
        # Преобразуем товары в dict, если это Pydantic модели
        products_dicts = []
        for product in products_list:
            if hasattr(product, "dict"):
                products_dicts.append(product.dict())
            elif hasattr(product, "model_dump"):
                products_dicts.append(product.model_dump())
            else:
                products_dicts.append(product)
        
        # Получаем веса товаров из БД
        from src.models.product import Product
        from sqlalchemy import select
        
        product_ids = [p.get("product_id") for p in products_dicts if p.get("product_id")]
        product_weights = {}
        if product_ids:
            products_result = await db.execute(
                select(Product).where(Product.id.in_(product_ids))
            )
            products = products_result.scalars().all()
            product_weights = {p.id: p.weight for p in products}
        
        for product in products_dicts:
            # Получаем цену (используем discount_price если есть, иначе price)
            price = product.get("discount_price") or product.get("price")
            # Конвертируем Decimal в float для payment.value
            price_float = float(price) if price else 0.0
            
            # Формируем ware_key: slug-color-size
            ware_key = f"{product.get('slug', '')}-{product.get('label', '').lower()}-{product.get('size', '').lower()}"
            
            # Получаем вес товара из БД, если доступен, иначе используем значение по умолчанию
            product_id = product.get("product_id")
            item_weight = product_weights.get(product_id, 500) if product_id and product_weights else 500  # вес одного товара в граммах
            
            item = {
                "name": f"{product.get('title', '')} ({product.get('label', '')}, {product.get('size', '')})",
                "ware_key": ware_key,
                "payment": {
                    "value": price_float,  # price float
                },
                "cost": int(price),  # price int
                "weight": item_weight,
                "amount": product.get("quantity", 1)
            }
            items.append(item)
            total_weight += item_weight * item["amount"]
        
        # Получаем данные получателя
        first_name = order_detail_dict.get("first_name", "")
        last_name = order_detail_dict.get("last_name", "")
        phone = order_detail_dict.get("phone") or "+79991234567"
        email = order_detail_dict.get("email")
        
        # Подготавливаем данные заказа
        order_data = {
            "type": 1,  # Всегда 1
            "number": str(order_id),  # order_id
            "tariff_code": 136,  # Посылка склад-склад 136
            "shipment_point": shipment_point,  # Код ПВЗ отправления
            "delivery_point": delivery_point,  # Код ПВЗ доставки
            "recipient": {
                "name": f"{first_name} {last_name}".strip(),
                "phones": [
                    {
                        "number": phone
                    }
                ]
            },
            "packages": [
                {
                    "number": str(order_id),  # order_id
                    "weight": total_weight,  # total weight in grams
                    "items": items
                }
            ]
        }
        
        # Добавляем email получателя, если есть
        if email:
            order_data["recipient"]["email"] = email
        
        # Отправляем запрос в CDEK
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/orders",
                    json=order_data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                response_data = response.json() if response.content else {}
                
                # Проверяем наличие ошибок
                if response.status_code != 200:
                    errors = response_data.get("errors", [])
                    if errors:
                        error_messages = [e.get("message", "Unknown error") for e in errors]
                        error_msg = "; ".join(error_messages)
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                    
                    logger.error(f"CDEK order creation failed: {error_msg}")
                    raise CDEKError(f"CDEK API error: {error_msg}")
                
                # Проверяем наличие ошибок в ответе
                if "errors" in response_data:
                    errors = response_data["errors"]
                    error_messages = [e.get("message", "Unknown error") for e in errors]
                    error_msg = "; ".join(error_messages)
                    logger.error(f"CDEK order creation returned errors: {error_msg}")
                    raise CDEKError(f"CDEK API error: {error_msg}")
                
                # Получаем UUID заказа
                cdek_uuid = response_data.get("entity", {}).get("uuid")
                if not cdek_uuid:
                    logger.error(f"CDEK order response missing uuid: {response_data}")
                    raise CDEKError("Invalid response from CDEK: missing uuid")
                
                # Сохраняем cdek_uuid в БД
                from src.models.orders import Order
                order = await db.get(Order, order_id)
                if order:
                    order.cdek_uuid = cdek_uuid
                    await db.commit()
                    logger.info(f"Updated order {order_id} with cdek_uuid: {cdek_uuid}")
                
                logger.info(f"CDEK order created successfully: {cdek_uuid}")
                return cdek_uuid
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while creating CDEK order: {str(e)}")
            raise CDEKError(f"CDEK order creation failed: {str(e)}")
        except CDEKError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while creating CDEK order: {str(e)}")
            raise CDEKError(f"CDEK order creation failed: {str(e)}")

    
    async def calculate_delivery_cost(
        self,
        from_location: Dict[str, Any],
        to_location: Dict[str, Any],
        packages: List[Dict[str, Any]],
        tariff_code: Optional[int] = None
    ) -> Dict[str, Any]:

        token = await self._get_access_token()
        
        request_data = {
            "from_location": from_location,
            "to_location": to_location,
            "packages": packages
        }
        
        if tariff_code:
            request_data["tariff_code"] = tariff_code
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/calculator/tarifflist",
                    json=request_data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK delivery calculation failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to calculate delivery cost: {response.status_code}")
                
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while calculating delivery cost: {str(e)}")
                raise CDEKError(f"Failed to calculate delivery cost: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error while calculating delivery cost: {str(e)}")
                raise CDEKError(f"Failed to calculate delivery cost: {str(e)}")
    
    async def get_suggest_cities(self, city_name: str) -> List[Dict[str, Any]]:
        # Нормализуем название города для кеша (приводим к нижнему регистру)
        cache_key = city_name.lower().strip()
        
        # Проверяем кеш (TTLCache автоматически проверяет TTL)
        if cache_key in self._cities_cache:
            logger.debug(f"Returning cached cities for '{city_name}'")
            return self._cities_cache[cache_key]
        
        # Получаем данные из API
        token = await self._get_access_token()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/location/suggest/cities",
                    params={"name": city_name},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK cities request failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to get suggest cities: {response.status_code}")
                
                result = response.json()
                
                # Сохраняем в кеш (TTLCache автоматически управляет временем жизни)
                self._cities_cache[cache_key] = result
                logger.debug(f"Cached cities for '{city_name}' (expires in 1 day)")
                
                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting suggest cities: {str(e)}")
            raise CDEKError(f"Failed to get suggest cities: {str(e)}")
        except CDEKError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting suggest cities: {str(e)}")
            raise CDEKError(f"Failed to get suggest cities: {str(e)}")

    async def get_offices_by_city_code(
        self, 
        city_code: int, 
        office_type: str = "PVZ"
    ) -> List[Dict[str, Any]]:
        # Используем комбинацию city_code и office_type как ключ кеша
        cache_key = f"{city_code}_{office_type}"
        
        # Проверяем кеш (TTLCache автоматически проверяет TTL)
        if cache_key in self._offices_cache:
            logger.debug(f"Returning cached offices for city_code={city_code}, type={office_type}")
            return self._offices_cache[cache_key]
        
        # Получаем данные из API
        token = await self._get_access_token()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/deliverypoints",
                    params={
                        "city_code": city_code,
                        "type": office_type
                    },
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK offices request failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to get offices: {response.status_code}")
                
                result = response.json()
                
                # Сохраняем в кеш (TTLCache автоматически управляет временем жизни)
                self._offices_cache[cache_key] = result
                logger.debug(f"Cached offices for city_code={city_code}, type={office_type} (expires in 1 day)")
                
                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting offices: {str(e)}")
            raise CDEKError(f"Failed to get offices: {str(e)}")
        except CDEKError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting offices: {str(e)}")
            raise CDEKError(f"Failed to get offices: {str(e)}")
    
    async def get_order_info_by_uuid(self, uuid: str) -> Dict[str, Any]:
        """
        Получить информацию о заказе в CDEK по UUID
        
        Args:
            uuid: UUID заказа в системе CDEK
            
        Returns:
            JSON ответ с информацией о заказе
            
        Raises:
            CDEKError: Если не удалось получить информацию о заказе
        """
        token = await self._get_access_token()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/orders/{uuid}",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK order info request failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to get order info: {response.status_code}")
                
                result = response.json()
                logger.debug(f"Retrieved order info for UUID: {uuid}")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while getting order info: {str(e)}")
            raise CDEKError(f"Failed to get order info: {str(e)}")
        except CDEKError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error while getting order info: {str(e)}")
            raise CDEKError(f"Failed to get order info: {str(e)}")


# Создаем глобальный экземпляр клиента (можно использовать как singleton)
_cdek_client: Optional[CDEKClient] = None


def get_cdek_client() -> CDEKClient:
    """
    Получить экземпляр CDEK клиента (singleton)
    
    Returns:
        Экземпляр CDEKClient
    """
    global _cdek_client
    if _cdek_client is None:
        _cdek_client = CDEKClient()
    return _cdek_client

