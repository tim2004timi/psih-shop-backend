# Документация API: Заказы

**Base URL:** `http://109.172.36.219:8000/api`

## Создание заказов

### 1. Создать заказ

**URL:** `POST /orders`

**Описание:** Создает новый заказ с товарами. Автоматически вычисляет `total_price` на основе цен товаров и проверяет наличие достаточного количества товаров. Доступно без аутентификации (гостевые заказы). Если пользователь авторизован, `user_id` будет установлен автоматически из токена.

**Аутентификация:** Опциональна (Bearer token). Если токен предоставлен, заказ будет привязан к пользователю.

**Входные данные (JSON):**
```json
{
  "order": {
    "email": "customer@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "city": "Moscow",
    "postal_code": "123456",
    "address": "Street Address 123",
    "status": "processing"
  },
  "products": [
    {
      "product_size_id": 1,
      "quantity": 2
    },
    {
      "product_size_id": 3,
      "quantity": 1
    }
  ]
}
```

**Обязательные поля:**
- `order.email` (string, максимум 100 символов) - Email покупателя
- `order.first_name` (string, максимум 50 символов) - Имя покупателя
- `order.last_name` (string, максимум 50 символов) - Фамилия покупателя
- `products` (array, минимум 1 элемент) - Список товаров в заказе

**Необязательные поля:**
- `order.phone` (string, максимум 15 символов) - Телефон покупателя
- `order.city` (string, максимум 50 символов) - Город доставки
- `order.postal_code` (string, максимум 10 символов) - Почтовый индекс
- `order.address` (string, максимум 200 символов) - Адрес доставки
- `order.status` (string, по умолчанию: "processing") - Статус заказа: `processing`, `shipped`, `delivered`, `cancelled`
- `order.user_id` (int) - ID пользователя (устанавливается автоматически, если пользователь авторизован)

**Поля товара в заказе:**
- `product_size_id` (int, обязательно) - ID размера продукта
- `quantity` (int, обязательно, больше 0) - Количество товара

**Выходные данные:**
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "city": "Moscow",
  "postal_code": "123456",
  "address": "Street Address 123",
  "total_price": "89.97",
  "delivery_method": "cdek",
  "status": "processing",
  "user_id": null,
  "created_at": "2024-01-15T10:30:00",
  "products": [
    {
      "id": 1,
      "product_id": 1,
      "product_color_id": 5,
      "slug": "basic-tshirt-red",
      "title": "Basic T-Shirt",
      "label": "Red",
      "hex": "#FF0000",
      "price": "29.99",
      "discount_price": "24.99",
      "currency": "EUR",
      "size": "M",
      "quantity": 2
    },
    {
      "id": 2,
      "product_id": 2,
      "product_color_id": 8,
      "slug": "premium-hoodie-blue",
      "title": "Premium Hoodie",
      "label": "Blue",
      "hex": "#0000FF",
      "price": "39.99",
      "discount_price": null,
      "currency": "EUR",
      "size": "L",
      "quantity": 1
    }
  ]
}
```

## Получение заказов

### 2. Получить список заказов

**URL:** `GET /orders`

**Описание:** Получает список всех заказов с полной информацией о товарах. Требуется аутентификация. Обычные пользователи видят только свои заказы, администраторы видят все заказы.

**Аутентификация:** Требуется (Bearer token)

**Входные данные (Query параметры):**
- `skip` (int, опционально, по умолчанию: 0) - Количество записей для пропуска
- `limit` (int, опционально, по умолчанию: 100, максимум: 1000) - Количество записей для возврата

**Выходные данные:**
```json
[
  {
    "id": 1,
    "email": "customer@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "city": "Moscow",
    "postal_code": "123456",
    "address": "Street Address 123",
    "total_price": "89.97",
    "delivery_method": "cdek",
    "status": "processing",
    "user_id": 1,
    "created_at": "2024-01-15T10:30:00",
    "products": [
      {
        "id": 1,
        "product_id": 1,
        "product_color_id": 5,
        "slug": "basic-tshirt-red",
        "title": "Basic T-Shirt",
        "label": "Red",
        "hex": "#FF0000",
        "price": "29.99",
        "discount_price": "24.99",
        "currency": "EUR",
        "size": "M",
        "quantity": 2
      }
    ]
  },
  {
    "id": 2,
    "email": "another@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+9876543210",
    "city": "Saint Petersburg",
    "postal_code": "190000",
    "address": "Nevsky Prospect 1",
    "total_price": "39.99",
    "delivery_method": "cdek",
    "status": "shipped",
    "user_id": null,
    "created_at": "2024-01-14T15:20:00",
    "products": [
      {
        "id": 3,
        "product_id": 2,
        "product_color_id": 8,
        "slug": "premium-hoodie-blue",
        "title": "Premium Hoodie",
        "label": "Blue",
        "hex": "#0000FF",
        "price": "39.99",
        "discount_price": null,
        "currency": "EUR",
        "size": "L",
        "quantity": 1
      }
    ]
  }
]
```

### 3. Получить заказ по ID

**URL:** `GET /orders/{order_id}`

**Описание:** Получает полную информацию о заказе по его ID, включая список товаров. Требуется аутентификация. Обычные пользователи могут видеть только свои заказы, администраторы могут видеть все заказы.

**Аутентификация:** Требуется (Bearer token)

**Входные данные (Path параметры):**
- `order_id` (int, обязательно) - ID заказа

**Выходные данные:**
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "city": "Moscow",
  "postal_code": "123456",
  "address": "Street Address 123",
  "total_price": "89.97",
  "delivery_method": "cdek",
  "status": "processing",
  "user_id": 1,
  "created_at": "2024-01-15T10:30:00",
  "products": [
    {
      "id": 1,
      "product_id": 1,
      "product_color_id": 5,
      "slug": "basic-tshirt-red",
      "title": "Basic T-Shirt",
      "label": "Red",
      "hex": "#FF0000",
      "price": "29.99",
      "discount_price": "24.99",
      "currency": "EUR",
      "size": "M",
      "quantity": 2
    },
    {
      "id": 2,
      "product_id": 2,
      "product_color_id": 8,
      "slug": "premium-hoodie-blue",
      "title": "Premium Hoodie",
      "label": "Blue",
      "hex": "#0000FF",
      "price": "39.99",
      "discount_price": null,
      "currency": "EUR",
      "size": "L",
      "quantity": 1
    }
  ]
}
```

## Управление заказами

### 4. Обновить статус заказа

**URL:** `PUT /orders/{order_id}`

**Описание:** Обновляет статус заказа. Доступно только администраторам. Можно изменить только статус заказа.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `order_id` (int, обязательно) - ID заказа

**Входные данные (JSON):**
```json
{
  "status": "shipped"
}
```

**Обязательные поля:**
- `status` (string, опционально) - Новый статус заказа: `processing`, `shipped`, `delivered`, `cancelled`

**Выходные данные:**
```json
{
  "id": 1,
  "email": "customer@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "city": "Moscow",
  "postal_code": "123456",
  "address": "Street Address 123",
  "total_price": "89.97",
  "delivery_method": "cdek",
  "status": "shipped",
  "user_id": 1,
  "created_at": "2024-01-15T10:30:00",
  "products": [
    {
      "id": 1,
      "product_id": 1,
      "product_color_id": 5,
      "slug": "basic-tshirt-red",
      "title": "Basic T-Shirt",
      "label": "Red",
      "hex": "#FF0000",
      "price": "29.99",
      "discount_price": "24.99",
      "currency": "EUR",
      "size": "M",
      "quantity": 2
    }
  ]
}
```

