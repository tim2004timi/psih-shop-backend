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
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:

        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            try:
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
                
                # Проверяем наличие entity в ответе
                if "entity" not in response_data:
                    logger.error(f"CDEK order response missing entity: {response_data}")
                    raise CDEKError("Invalid response from CDEK: missing entity")
                
                order_uuid = response_data.get("entity", {}).get("uuid")
                logger.info(f"CDEK order created successfully: {order_uuid}")
                return response_data
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while creating CDEK order: {str(e)}")
                raise CDEKError(f"CDEK order creation failed: {str(e)}")
            except CDEKError:
                raise
            except Exception as e:
                logger.error(f"Unexpected error while creating CDEK order: {str(e)}")
                raise CDEKError(f"CDEK order creation failed: {str(e)}")
    
    async def get_order_status(self, order_uuid: str) -> Dict[str, Any]:

        token = await self._get_access_token()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/orders/{order_uuid}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    },
                    timeout=10.0
                )
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"CDEK order status request failed: {response.status_code} - {error_text}")
                    raise CDEKError(f"Failed to get CDEK order status: {response.status_code}")
                
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error while getting CDEK order status: {str(e)}")
                raise CDEKError(f"Failed to get CDEK order status: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error while getting CDEK order status: {str(e)}")
                raise CDEKError(f"Failed to get CDEK order status: {str(e)}")
    
    def prepare_order_data(
        self,
        order_id: int,
        recipient_name: str,
        recipient_phone: str,
        recipient_email: Optional[str],
        city: str = "Москва",
        address: Optional[str] = None,
        postal_code: Optional[str] = None,
        products: Optional[List[Dict[str, Any]]] = None,
        sender_info: Optional[Dict[str, Any]] = None,
        tariff_code: int = 136,
        comment: Optional[str] = None,
        from_city: str = "Москва",
        from_country_code: str = "RU"
    ) -> Dict[str, Any]:
        
        # Подготовка товаров
        items = []
        total_weight = 0
        
        if products:
            for idx, product in enumerate(products, 1):
                # Получаем стоимость в копейках
                cost = product.get("cost", 0)
                if isinstance(cost, (Decimal, float)):
                    cost_in_kopecks = int(cost * 100)
                elif isinstance(cost, int):
                    cost_in_kopecks = cost * 100  # Предполагаем, что это рубли
                else:
                    cost_in_kopecks = 0
                
                item = {
                    "name": product.get("name", f"Товар {idx}"),
                    "ware_key": product.get("ware_key", f"PROD-{idx}"),
                    "payment": {
                        "value": cost_in_kopecks,
                        "vat_sum": 0,
                        "vat_rate": 0
                    },
                    "cost": cost_in_kopecks,
                    "amount": product.get("amount", 1),
                    "weight": product.get("weight", 500)  # Вес в граммах
                }
                
                # Добавляем URL товара, если указан
                if "url" in product:
                    item["url"] = product["url"]
                
                items.append(item)
                total_weight += item["weight"] * item["amount"]
        else:
            # Если товары не указаны, создаем пустую посылку с минимальным весом
            total_weight = 500
        
        # Формируем данные заказа
        order_data = {
            "type": 1,  # Интернет-магазин
            "number": str(order_id),
            # TODO: "shipment_point"
            # "comment": comment or f"Заказ #{order_id}",
            "recipient": {
                "name": recipient_name,
                "phones": [{"number": recipient_phone}],
                "email": recipient_email
            },
            "delivery_recipient_cost": {
                "value": 0  # Доставка оплачена отправителем
            },
            "delivery_recipient_cost_adv": [
                {
                    "sum": 0,
                    "vat_sum": 0,
                    "vat_rate": 0
                }
            ],
            "from_location": {
                "city": from_city,
                "country_code": from_country_code
            },
            "to_location": {
                "city": city,
                "country_code": "RU"
            },
            "packages": [
                {
                    "number": f"PACK-{order_id}",
                    "weight": max(total_weight, 500),  # Минимум 500 грамм
                    "length": 30,  # Габариты можно вычислить или задать по умолчанию
                    "width": 20,
                    "height": 15,
                    "items": items
                }
            ],
            "tariff_code": tariff_code
        }
        
        # Добавляем email получателя, если указан
        if recipient_email:
            order_data["recipient"]["email"] = recipient_email
        
        # Добавляем адрес доставки, если указан
        if address:
            order_data["to_location"]["address"] = address
        
        # Добавляем почтовый индекс, если указан
        if postal_code:
            order_data["to_location"]["postal_code"] = postal_code
        
        return order_data
    
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

