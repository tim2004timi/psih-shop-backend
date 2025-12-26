# Интеграция с CDEK API

**Документация CDEK API:** https://apidoc.cdek.ru/

## Обзор

Данная документация описывает процесс интеграции интернет-магазина с API СДЭК для автоматизации создания заказов на доставку. Когда клиент оформляет заказ в вашем магазине, система автоматически создает заказ в системе СДЭК.

## Краткая сводка процесса

1. **Клиент оформляет заказ** → Ваш backend создает заказ в БД через `POST /api/orders`
2. **После создания заказа** → Система автоматически вызывает CDEK API для создания заказа на доставку
3. **CDEK возвращает UUID заказа** → Сохраняем его в БД для отслеживания
4. **Отслеживание статуса** → Периодически проверяем статус заказа через `GET /v2/orders/{uuid}`

**Основной endpoint CDEK для создания заказа:** `POST https://api.cdek.ru/v2/orders`

## Подготовка

### 1. Получение учетных данных

Для работы с CDEK API необходимо:

1. **Заключить договор с СДЭК** - это даст доступ к личному кабинету
2. **Получить учетные данные** в личном кабинете СДЭК:
   - `account` - идентификатор аккаунта
   - `secure_password` - секретный пароль для API

Эти данные понадобятся для аутентификации при каждом запросе к API.

### 2. Настройка переменных окружения

Добавьте в файл `.env` следующие переменные:

```env
CDEK_ACCOUNT=your_account_id
CDEK_SECURE_PASSWORD=your_secure_password
CDEK_API_URL=https://api.cdek.ru/v2
CDEK_TEST_MODE=true  # Используйте true для тестирования
```

## Процесс создания заказа: пошаговый пример

### Сценарий: Клиент делает заказ в интернет-магазине

**Шаг 1:** Клиент заполняет форму заказа в вашем интернет-магазине:

```json
{
  "order": {
    "email": "ivan.petrov@example.com",
    "first_name": "Иван",
    "last_name": "Петров",
    "phone": "+79991234567",
    "city": "Москва",
    "postal_code": "101000",
    "address": "ул. Тверская, д. 10, кв. 5"
  },
  "products": [
    {
      "product_size_id": 1,
      "quantity": 2
    },
    {
      "product_size_id": 5,
      "quantity": 1
    }
  ]
}
```

**Шаг 2:** Ваш backend создает заказ в своей базе данных через `POST /api/orders`

**Шаг 3:** После успешного создания заказа в вашей БД, система автоматически создает заказ в СДЭК через их API.

### Endpoint для создания заказа в CDEK

**URL:** `POST https://api.cdek.ru/v2/orders`

**Аутентификация:** OAuth 2.0 (необходимо получить токен перед запросом)

**Заголовки:**
```
Content-Type: application/json
Authorization: Bearer {access_token}
```

### Структура запроса к CDEK API

```json
{
  "type": 1,
  "number": "ORDER-2024-001",
  "date_invoice": "2024-01-15",
  "comment": "Заказ из интернет-магазина",
  "sender": {
    "company": "Ваш интернет-магазин",
    "name": "Иван Иванов",
    "email": "shop@example.com",
    "phones": [
      {
        "number": "+79991234567"
      }
    ]
  },
  "recipient": {
    "name": "Иван Петров",
    "phones": [
      {
        "number": "+79991234567"
      }
    ],
    "email": "ivan.petrov@example.com"
  },
  "delivery_recipient_cost": {
    "value": 0
  },
  "delivery_recipient_cost_adv": [
    {
      "sum": 0,
      "vat_sum": 0,
      "vat_rate": 0
    }
  ],
  "from_location": {
    "code": 270,
    "city": "Москва",
    "country_code": "RU"
  },
  "to_location": {
    "code": 270,
    "city": "Москва",
    "address": "ул. Тверская, д. 10, кв. 5",
    "postal_code": "101000",
    "country_code": "RU"
  },
  "packages": [
    {
      "number": "PACK-001",
      "weight": 1500,
      "length": 30,
      "width": 20,
      "height": 15,
      "items": [
        {
          "name": "Basic T-Shirt (Red, M)",
          "ware_key": "PROD-001-M-RED",
          "payment": {
            "value": 2499,
            "vat_sum": 0,
            "vat_rate": 0
          },
          "cost": 2499,
          "amount": 2,
          "weight": 500,
          "url": "https://yourshop.com/products/basic-tshirt-red"
        },
        {
          "name": "Premium Hoodie (Blue, L)",
          "ware_key": "PROD-005-L-BLUE",
          "payment": {
            "value": 3999,
            "vat_sum": 0,
            "vat_rate": 0
          },
          "cost": 3999,
          "amount": 1,
          "weight": 500,
          "url": "https://yourshop.com/products/premium-hoodie-blue"
        }
      ]
    }
  ],
  "tariff_code": 136
}
```

### Описание полей запроса

#### Основные поля заказа

- **`type`** (int, обязательно): Тип заказа
  - `1` - интернет-магазин
  - `2` - доставка
  - `3` - экспресс-доставка

- **`number`** (string, обязательно): Уникальный номер заказа в вашей системе
  - Формат: `"ORDER-{year}-{number}"` или просто `"{order_id}"`
  - Пример: `"ORDER-2024-001"` или `"123"`

- **`date_invoice`** (string, формат YYYY-MM-DD): Дата оформления заказа

- **`comment`** (string, опционально): Комментарий к заказу

#### Информация об отправителе (`sender`)

- **`company`** (string): Название вашей компании
- **`name`** (string): Имя контактного лица
- **`email`** (string): Email отправителя
- **`phones`** (array): Массив телефонов
  ```json
  {
    "number": "+79991234567"
  }
  ```

#### Информация о получателе (`recipient`)

- **`name`** (string, обязательно): ФИО получателя (объедините `first_name` и `last_name`)
- **`phones`** (array, обязательно): Массив телефонов получателя
- **`email`** (string, опционально): Email получателя

#### Локации (`from_location` и `to_location`)

- **`code`** (int): Код города по справочнику CDEK (можно получить через API)
- **`city`** (string): Название города
- **`address`** (string, для `to_location`): Полный адрес доставки
- **`postal_code`** (string): Почтовый индекс
- **`country_code`** (string): Код страны (например, `"RU"`)

#### Посылки (`packages`)

Массив посылок в заказе. Каждая посылка содержит:

- **`number`** (string): Уникальный номер посылки
- **`weight`** (int): Общий вес посылки в граммах
- **`length`**, **`width`**, **`height`** (int): Габариты в сантиметрах

**Товары в посылке (`items`):**

- **`name`** (string): Название товара (можно добавить размер и цвет)
- **`ware_key`** (string): Артикул/SKU товара в вашей системе
- **`payment`** (object): Информация об оплате
  - `value` (int): Сумма к оплате в копейках (например, 2499 = 24.99 руб)
  - `vat_sum` (int): Сумма НДС в копейках (0 если без НДС)
  - `vat_rate` (int): Ставка НДС (0, 10, 20)
- **`cost`** (int): Стоимость товара в копейках
- **`amount`** (int): Количество единиц товара
- **`weight`** (int): Вес одной единицы в граммах
- **`url`** (string, опционально): Ссылка на товар в вашем магазине

#### Тариф доставки

- **`tariff_code`** (int, обязательно): Код тарифа доставки
  - `136` - Посылка склад-склад
  - `137` - Посылка склад-дверь
  - `138` - Посылка дверь-склад
  - `139` - Посылка дверь-дверь
  - `233` - Экономичная посылка склад-склад
  - `234` - Экономичная посылка склад-дверь
  - И другие (см. документацию CDEK)

#### Стоимость доставки

- **`delivery_recipient_cost`** (object): Стоимость доставки, оплачиваемая получателем
  - `value` (int): Сумма в копейках (0 если доставка оплачена отправителем)

### Пример ответа от CDEK API

При успешном создании заказа CDEK вернет:

```json
{
  "entity": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "request_uuid": "550e8400-e29b-41d4-a716-446655440001",
    "type": 1,
    "cdek_number": "CDEK-1234567890",
    "number": "ORDER-2024-001",
    "tariff_code": 136,
    "comment": "Заказ из интернет-магазина",
    "shipment_point": "MSK-1",
    "delivery_point": null,
    "date_invoice": "2024-01-15",
    "shipper_name": "Ваш интернет-магазин",
    "shipper_address": {
      "code": 270,
      "city": "Москва",
      "country_code": "RU"
    },
    "delivery_recipient_cost": {
      "value": 0
    },
    "recipient": {
      "name": "Иван Петров",
      "phones": [
        {
          "number": "+79991234567"
        }
      ],
      "email": "ivan.petrov@example.com"
    },
    "from_location": {
      "code": 270,
      "city": "Москва",
      "country_code": "RU"
    },
    "to_location": {
      "code": 270,
      "city": "Москва",
      "address": "ул. Тверская, д. 10, кв. 5",
      "postal_code": "101000",
      "country_code": "RU"
    },
    "packages": [
      {
        "number": "PACK-001",
        "uuid": "550e8400-e29b-41d4-a716-446655440002",
        "weight": 1500,
        "length": 30,
        "width": 20,
        "height": 15,
        "items": [
          {
            "name": "Basic T-Shirt (Red, M)",
            "ware_key": "PROD-001-M-RED",
            "payment": {
              "value": 2499,
              "vat_sum": 0,
              "vat_rate": 0
            },
            "cost": 2499,
            "amount": 2,
            "weight": 500
          },
          {
            "name": "Premium Hoodie (Blue, L)",
            "ware_key": "PROD-005-L-BLUE",
            "payment": {
              "value": 3999,
              "vat_sum": 0,
              "vat_rate": 0
            },
            "cost": 3999,
            "amount": 1,
            "weight": 500
          }
        ]
      }
    ],
    "statuses": [
      {
        "code": "ACCEPTED",
        "name": "Принят",
        "date_time": "2024-01-15T10:30:00+00:00"
      }
    ],
    "created_date": "2024-01-15T10:30:00+00:00"
  },
  "requests": [
    {
      "request_uuid": "550e8400-e29b-41d4-a716-446655440001",
      "type": "CREATE",
      "date_time": "2024-01-15T10:30:00+00:00",
      "state": "ACCEPTED"
    }
  ]
}
```

### Важные поля в ответе

- **`entity.uuid`** - Уникальный идентификатор заказа в системе CDEK (сохраните его!)
- **`entity.cdek_number`** - Номер заказа в системе CDEK (для отслеживания)
- **`entity.number`** - Ваш номер заказа (который вы передали)
- **`entity.statuses`** - Массив статусов заказа

## Полный процесс интеграции

### 1. Получение OAuth токена

Перед созданием заказа необходимо получить токен доступа:

**Endpoint:** `POST https://api.cdek.ru/v2/oauth/token`

**Заголовки:**
```
Content-Type: application/x-www-form-urlencoded
```

**Тело запроса (form-data):**
```
grant_type=client_credentials
client_id={CDEK_ACCOUNT}
client_secret={CDEK_SECURE_PASSWORD}
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "orders"
}
```

Токен действителен 1 час (3600 секунд). Сохраните его и используйте для всех запросов.

### 2. Создание заказа в CDEK

После получения токена создайте заказ через `POST /v2/orders` с данными, описанными выше.

### 3. Сохранение информации о заказе CDEK

После успешного создания заказа в CDEK сохраните в вашей БД:
- `cdek_uuid` - UUID заказа в системе CDEK
- `cdek_number` - Номер заказа CDEK
- `cdek_tracking_url` - URL для отслеживания (можно сформировать)

### 4. Отслеживание статуса заказа

**Endpoint:** `GET https://api.cdek.ru/v2/orders/{uuid}`

**Заголовки:**
```
Authorization: Bearer {access_token}
```

Этот endpoint позволяет получить актуальный статус заказа по его UUID.

## Обработка ошибок

CDEK API может вернуть ошибки. Примеры:

```json
{
  "errors": [
    {
      "code": "invalid_input",
      "message": "Неверный формат данных",
      "details": {
        "field": "recipient.phones",
        "message": "Телефон обязателен"
      }
    }
  ]
}
```

Всегда проверяйте наличие поля `errors` в ответе и обрабатывайте их соответствующим образом.

## Рекомендации по реализации

1. **Асинхронная обработка**: Создание заказа в CDEK лучше делать асинхронно (через фоновую задачу), чтобы не блокировать ответ клиенту.

2. **Retry механизм**: Добавьте повторные попытки при временных ошибках (сетевые проблемы, таймауты).

3. **Логирование**: Логируйте все запросы и ответы для отладки.

4. **Валидация данных**: Проверяйте данные перед отправкой в CDEK API.

5. **Кэширование токенов**: Кэшируйте OAuth токены и обновляйте их при истечении.

6. **Обработка вебхуков**: CDEK может отправлять уведомления об изменении статуса заказа через вебхуки. Настройте endpoint для их приема.

## Дополнительные возможности CDEK API

- **Расчет стоимости доставки**: `POST /v2/calculator/tarifflist` - расчет стоимости доставки
- **Список пунктов выдачи**: `GET /v2/deliverypoints` - получение списка ПВЗ
- **Список городов**: `GET /v2/location/cities` - получение списка городов
- **Печать накладных**: `GET /v2/orders/{uuid}/print` - получение накладной для печати

Подробнее в официальной документации: https://apidoc.cdek.ru/

## Пример реализации модуля для работы с CDEK API

Ниже приведен пример кода для интеграции с CDEK API на Python:

### 1. Создание модуля `src/services/cdek.py`

```python
import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from src.config import settings

logger = logging.getLogger(__name__)

class CDEKClient:
    """Клиент для работы с CDEK API"""
    
    def __init__(
        self,
        account: Optional[str] = None,
        secure_password: Optional[str] = None,
        api_url: str = "https://api.cdek.ru/v2",
        test_mode: bool = False
    ):
        self.account = account or getattr(settings, 'CDEK_ACCOUNT', None)
        self.secure_password = secure_password or getattr(settings, 'CDEK_SECURE_PASSWORD', None)
        self.api_url = api_url
        self.test_mode = test_mode
        
        if test_mode:
            self.api_url = "https://api.edu.cdek.ru/v2"
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        if not self.account or not self.secure_password:
            raise ValueError("CDEK_ACCOUNT and CDEK_SECURE_PASSWORD must be set")
    
    async def _get_access_token(self) -> str:
        """Получить OAuth токен доступа"""
        # Проверяем, не истек ли текущий токен
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at - timedelta(minutes=5):
                return self._access_token
        
        # Получаем новый токен
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/oauth/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.account,
                        "client_secret": self.secure_password
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("CDEK access token obtained successfully")
                return self._access_token
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to get CDEK access token: {str(e)}")
                raise Exception(f"CDEK authentication failed: {str(e)}")
    
    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создать заказ в CDEK
        
        Args:
            order_data: Данные заказа в формате CDEK API
            
        Returns:
            Ответ от CDEK API с информацией о созданном заказе
        """
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
                
                # Проверяем наличие ошибок
                if response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    errors = error_data.get("errors", [])
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in errors])
                    raise Exception(f"CDEK API error: {error_msg}")
                
                data = response.json()
                
                # Проверяем наличие ошибок в ответе
                if "errors" in data:
                    errors = data["errors"]
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in errors])
                    raise Exception(f"CDEK API error: {error_msg}")
                
                logger.info(f"CDEK order created: {data.get('entity', {}).get('uuid')}")
                return data
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to create CDEK order: {str(e)}")
                raise Exception(f"CDEK order creation failed: {str(e)}")
    
    async def get_order_status(self, order_uuid: str) -> Dict[str, Any]:
        """
        Получить статус заказа по UUID
        
        Args:
            order_uuid: UUID заказа в системе CDEK
            
        Returns:
            Информация о заказе и его статусе
        """
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
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"Failed to get CDEK order status: {str(e)}")
                raise Exception(f"Failed to get CDEK order status: {str(e)}")
    
    def prepare_order_data(
        self,
        order_id: int,
        recipient_name: str,
        recipient_phone: str,
        recipient_email: Optional[str],
        city: str,
        address: str,
        postal_code: Optional[str],
        products: list,
        sender_info: Optional[Dict[str, Any]] = None,
        tariff_code: int = 136,
        comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Подготовить данные заказа для отправки в CDEK API
        
        Args:
            order_id: ID заказа в вашей системе
            recipient_name: ФИО получателя
            recipient_phone: Телефон получателя
            recipient_email: Email получателя
            city: Город доставки
            address: Адрес доставки
            postal_code: Почтовый индекс
            products: Список товаров (каждый товар должен содержать name, ware_key, cost, amount, weight)
            sender_info: Информация об отправителе (по умолчанию из настроек)
            tariff_code: Код тарифа доставки (136 - посылка склад-склад)
            comment: Комментарий к заказу
            
        Returns:
            Словарь с данными заказа в формате CDEK API
        """
        # Информация об отправителе (можно вынести в настройки)
        default_sender = {
            "company": "Ваш интернет-магазин",
            "name": "Иван Иванов",
            "email": "shop@example.com",
            "phones": [{"number": "+79991234567"}]
        }
        sender = sender_info or default_sender
        
        # Подготовка товаров
        items = []
        total_weight = 0
        
        for idx, product in enumerate(products, 1):
            item = {
                "name": product.get("name", f"Товар {idx}"),
                "ware_key": product.get("ware_key", f"PROD-{idx}"),
                "payment": {
                    "value": int(product.get("cost", 0) * 100),  # Конвертируем в копейки
                    "vat_sum": 0,
                    "vat_rate": 0
                },
                "cost": int(product.get("cost", 0) * 100),  # Конвертируем в копейки
                "amount": product.get("amount", 1),
                "weight": product.get("weight", 500)  # Вес в граммах
            }
            items.append(item)
            total_weight += item["weight"] * item["amount"]
        
        # Формируем данные заказа
        order_data = {
            "type": 1,  # Интернет-магазин
            "number": f"ORDER-{order_id}",
            "date_invoice": datetime.now().strftime("%Y-%m-%d"),
            "comment": comment or f"Заказ #{order_id}",
            "sender": sender,
            "recipient": {
                "name": recipient_name,
                "phones": [{"number": recipient_phone}],
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
                "city": "Москва",  # Город отправления (из настроек)
                "country_code": "RU"
            },
            "to_location": {
                "city": city,
                "address": address,
                "country_code": "RU"
            },
            "packages": [
                {
                    "number": f"PACK-{order_id}",
                    "weight": total_weight,
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
        
        # Добавляем почтовый индекс, если указан
        if postal_code:
            order_data["to_location"]["postal_code"] = postal_code
        
        return order_data
```

### 2. Использование в роутере заказов

Пример интеграции в `src/routers/orders.py`:

```python
from src.services.cdek import CDEKClient
import asyncio

# В функции create_order после успешного создания заказа в БД:

async def create_order_with_cdek(
    order_request: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_optional_current_user)
):
    # ... существующий код создания заказа ...
    
    try:
        order = await crud.create_order(
            db=db,
            order_data=order_request.order,
            products=order_request.products
        )
        
        # Получаем детальную информацию о заказе
        order_detail = await crud.get_order_detail(db, order.id)
        
        # Создаем заказ в CDEK асинхронно (не блокируем ответ)
        asyncio.create_task(create_cdek_order(order, order_detail))
        
        return order_detail
    except Exception as e:
        # ... обработка ошибок ...

async def create_cdek_order(order: Order, order_detail: OrderDetail):
    """Создать заказ в CDEK (фоновая задача)"""
    try:
        cdek_client = CDEKClient()
        
        # Подготавливаем данные товаров
        products = []
        for product in order_detail.products:
            products.append({
                "name": f"{product.title} ({product.label}, {product.size})",
                "ware_key": f"PROD-{product.product_id}-{product.product_color_id}-{product.size}",
                "cost": float(product.discount_price or product.price),
                "amount": product.quantity,
                "weight": 500  # Вес одного товара в граммах (можно вынести в настройки)
            })
        
        # Подготавливаем данные заказа
        cdek_order_data = cdek_client.prepare_order_data(
            order_id=order.id,
            recipient_name=f"{order.first_name} {order.last_name}",
            recipient_phone=order.phone or "",
            recipient_email=order.email,
            city=order.city or "Москва",
            address=order.address or "",
            postal_code=order.postal_code,
            products=products,
            comment=f"Заказ #{order.id} из интернет-магазина"
        )
        
        # Создаем заказ в CDEK
        cdek_response = await cdek_client.create_order(cdek_order_data)
        
        # Сохраняем UUID заказа CDEK в БД (нужно добавить поле cdek_uuid в модель Order)
        # await crud.update_order_cdek_uuid(db, order.id, cdek_response["entity"]["uuid"])
        
        logger.info(f"CDEK order created for order {order.id}: {cdek_response['entity']['uuid']}")
        
    except Exception as e:
        logger.error(f"Failed to create CDEK order for order {order.id}: {str(e)}")
        # Можно отправить уведомление администратору или сохранить ошибку в БД
```

### 3. Добавление зависимостей

Установите `httpx` для асинхронных HTTP запросов:

```bash
pip install httpx
```

Добавьте в `requirements.txt`:
```
httpx>=0.24.0
```

### 4. Настройка переменных окружения

Добавьте в `.env`:
```env
CDEK_ACCOUNT=your_account_id
CDEK_SECURE_PASSWORD=your_secure_password
CDEK_API_URL=https://api.cdek.ru/v2
CDEK_TEST_MODE=false
```

### 5. Обновление модели Order (опционально)

Для сохранения информации о заказе CDEK добавьте поля в модель:

```python
# В src/models/orders.py
cdek_uuid = Column(String(36), nullable=True, index=True)  # UUID заказа в CDEK
cdek_number = Column(String(50), nullable=True)  # Номер заказа CDEK
cdek_tracking_url = Column(String(255), nullable=True)  # URL для отслеживания
```

Это позволит отслеживать связь между заказами в вашей системе и заказами в CDEK.

