# Документация по остальным эндпоинтам продуктов (POST, PUT, DELETE)

## Обзор

Документация для всех эндпоинтов продуктов, требующих аутентификации (только для админов).

**Базовый URL:** `http://localhost:8000/api`

## Создание и управление продуктами

### 1. Создать новый продукт

**POST** `/api/products`

Создает новый продукт. Требует права администратора.

#### Запрос
```http
POST /api/products
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "id": "psih-basic-tshirt",
  "slug": "basic-tshirt",
  "title": "BASIC T-SHIRT",
  "description": "Классическая футболка из мягкого хлопка",
  "price": 120.00,
  "currency": "EUR",
  "composition": "100% cotton",
  "fit": "regular",
  "status": "in_stock",
  "is_pre_order": false,
  "meta_care": "Machine wash cold",
  "meta_shipping": "2-4 days",
  "meta_returns": "14 days"
}
```

**Обязательные поля:**
- `id` (string, max 50) - Уникальный ID продукта
- `slug` (string, max 100) - Уникальный slug для URL
- `title` (string, max 200) - Название продукта
- `price` (decimal) - Цена продукта

**Необязательные поля:**
- `description` (string) - Описание продукта
- `currency` (string, max 3) - Валюта (по умолчанию "EUR")
- `composition` (string, max 200) - Состав продукта
- `fit` (string, max 50) - Посадка/размер
- `status` (enum) - Статус: "in_stock", "out_of_stock", "discontinued" (по умолчанию "in_stock")
- `is_pre_order` (boolean) - Доступен ли для предзаказа (по умолчанию false)
- `meta_care` (string, max 200) - Инструкции по уходу
- `meta_shipping` (string, max 100) - Информация о доставке
- `meta_returns` (string, max 100) - Информация о возврате

#### Ответ
```json
{
  "id": "psih-basic-tshirt",
  "slug": "basic-tshirt",
  "title": "BASIC T-SHIRT",
  "categoryPath": [],
  "price": 120.00,
  "currency": "EUR",
  "colors": [],
  "sizes": [],
  "composition": "100% cotton",
  "fit": "regular",
  "description": "Классическая футболка из мягкого хлопка",
  "images": [],
  "meta": {
    "care": "Machine wash cold",
    "shipping": "2-4 days",
    "returns": "14 days"
  },
  "status": "in_stock"
}
```

#### Ошибки
- `400 Bad Request` - Продукт с таким ID или slug уже существует
- `403 Forbidden` - Требуются права администратора
- `422 Unprocessable Entity` - Ошибка валидации данных

### 2. Обновить продукт

**PUT** `/api/products/{product_id}`

Обновляет информацию о продукте. Требует права администратора.

#### Запрос
```http
PUT /api/products/psih-basic-tshirt
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "title": "BASIC T-SHIRT UPDATED",
  "price": 130.00,
  "description": "Обновленное описание футболки",
  "meta_care": "Hand wash only"
}
```

**Все поля необязательные:**
- `slug` (string, max 100) - Новый slug
- `title` (string, max 200) - Новое название
- `description` (string) - Новое описание
- `price` (decimal) - Новая цена
- `currency` (string, max 3) - Новая валюта
- `composition` (string, max 200) - Новый состав
- `fit` (string, max 50) - Новая посадка
- `status` (enum) - Новый статус
- `is_pre_order` (boolean) - Новый статус предзаказа
- `meta_care` (string, max 200) - Новые инструкции по уходу
- `meta_shipping` (string, max 100) - Новая информация о доставке
- `meta_returns` (string, max 100) - Новая информация о возврате

#### Ответ
```json
{
  "id": "psih-basic-tshirt",
  "slug": "basic-tshirt",
  "title": "BASIC T-SHIRT UPDATED",
  "categoryPath": [],
  "price": 130.00,
  "currency": "EUR",
  "colors": [
    {
      "code": "white",
      "label": "White",
      "hex": "#FFFFFF"
    }
  ],
  "sizes": ["S", "M", "L", "XL"],
  "composition": "100% cotton",
  "fit": "regular",
  "description": "Обновленное описание футболки",
  "images": [
    {
      "file": "http://localhost:9000/photos/uuid-123.jpg",
      "alt": null,
      "w": null,
      "h": null,
      "color": null
    }
  ],
  "meta": {
    "care": "Hand wash only",
    "shipping": "2-4 days",
    "returns": "14 days"
  },
  "status": "in_stock"
}
```

#### Ошибки
- `400 Bad Request` - Slug уже существует
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден
- `422 Unprocessable Entity` - Ошибка валидации данных

### 3. Удалить продукт

**DELETE** `/api/products/{product_id}`

Удаляет продукт. Требует права администратора.

#### Запрос
```http
DELETE /api/products/psih-basic-tshirt
Authorization: Bearer your_jwt_token
```

#### Ответ
```json
{
  "message": "Product deleted successfully"
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден

### 4. Изменить статус продукта

**PUT** `/api/products/{product_id}/status`

Изменяет статус продукта. Требует права администратора.

#### Запрос
```http
PUT /api/products/psih-basic-tshirt/status
Authorization: Bearer your_jwt_token
Content-Type: application/json

"out_of_stock"
```

**Возможные значения статуса:**
- `"in_stock"` - В наличии
- `"out_of_stock"` - Нет в наличии
- `"discontinued"` - Снят с производства

#### Ответ
```json
{
  "id": "psih-basic-tshirt",
  "slug": "basic-tshirt",
  "title": "BASIC T-SHIRT",
  "categoryPath": [],
  "price": 120.00,
  "currency": "EUR",
  "colors": [
    {
      "code": "white",
      "label": "White",
      "hex": "#FFFFFF"
    }
  ],
  "sizes": ["S", "M", "L", "XL"],
  "composition": "100% cotton",
  "fit": "regular",
  "description": "Классическая футболка из мягкого хлопка",
  "images": [],
  "meta": {
    "care": "Machine wash cold",
    "shipping": "2-4 days",
    "returns": "14 days"
  },
  "status": "out_of_stock"
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден
- `422 Unprocessable Entity` - Неверный статус

### 5. Переключить предзаказ

**PUT** `/api/products/{product_id}/toggle-preorder`

Переключает возможность предзаказа для продукта. Требует права администратора.

#### Запрос
```http
PUT /api/products/psih-basic-tshirt/toggle-preorder
Authorization: Bearer your_jwt_token
```

#### Ответ
```json
{
  "id": "psih-basic-tshirt",
  "slug": "basic-tshirt",
  "title": "BASIC T-SHIRT",
  "categoryPath": [],
  "price": 120.00,
  "currency": "EUR",
  "colors": [
    {
      "code": "white",
      "label": "White",
      "hex": "#FFFFFF"
    }
  ],
  "sizes": ["S", "M", "L", "XL"],
  "composition": "100% cotton",
  "fit": "regular",
  "description": "Классическая футболка из мягкого хлопка",
  "images": [],
  "meta": {
    "care": "Machine wash cold",
    "shipping": "2-4 days",
    "returns": "14 days"
  },
  "status": "in_stock"
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден

## Управление цветами продуктов

### 6. Добавить цвет продукта

**POST** `/api/products/{product_id}/colors`

Добавляет цвет к продукту. Требует права администратора.

#### Запрос
```http
POST /api/products/psih-basic-tshirt/colors
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "id": "color-uuid-123",
  "code": "navy",
  "label": "Navy Blue",
  "hex": "#1B365D"
}
```

**Обязательные поля:**
- `id` (string) - Уникальный ID цвета
- `code` (string) - Код цвета (например, "navy")
- `label` (string) - Отображаемое название (например, "Navy Blue")
- `hex` (string) - HEX код цвета (например, "#1B365D")

#### Ответ
```json
{
  "id": "color-uuid-123",
  "code": "navy",
  "label": "Navy Blue",
  "hex": "#1B365D"
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден
- `422 Unprocessable Entity` - Ошибка валидации данных

### 7. Удалить цвет продукта

**DELETE** `/api/products/colors/{color_id}`

Удаляет цвет продукта. Требует права администратора.

#### Запрос
```http
DELETE /api/products/colors/color-uuid-123
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Цвет не найден

## Управление размерами продуктов

### 8. Добавить размер продукта

**POST** `/api/products/{product_id}/sizes`

Добавляет размер к продукту. Требует права администратора.

#### Запрос
```http
POST /api/products/psih-basic-tshirt/sizes
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "id": "size-uuid-123",
  "size": "XXL"
}
```

**Обязательные поля:**
- `id` (string) - Уникальный ID размера
- `size` (string) - Размер (например, "XXL")

#### Ответ
```json
{
  "id": "size-uuid-123",
  "size": "XXL"
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден
- `422 Unprocessable Entity` - Ошибка валидации данных

### 9. Удалить размер продукта

**DELETE** `/api/products/sizes/{size_id}`

Удаляет размер продукта. Требует права администратора.

#### Запрос
```http
DELETE /api/products/sizes/size-uuid-123
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Размер не найден

## Управление изображениями продуктов

### 10. Загрузить изображение продукта

**POST** `/api/products/{product_id}/images`

Загружает изображение для продукта. Требует права администратора.

#### Запрос
```http
POST /api/products/psih-basic-tshirt/images
Authorization: Bearer your_jwt_token
Content-Type: multipart/form-data

sort_order: 0
file: [binary image data]
```

**Параметры:**
- `sort_order` (integer, optional) - Порядок сортировки изображения (по умолчанию 0)
- `file` (file, required) - Файл изображения

#### Ответ
```json
{
  "id": "image-uuid-123",
  "file": "http://localhost:9000/photos/uuid-123.jpg",
  "sort_order": 0
}
```

**Примечание:** При загрузке изображения автоматически создаются три версии:
- Оригинал: `uuid.jpg`
- Medium: `uuid-medium.jpg`
- Small: `uuid-small.jpg`

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт не найден
- `422 Unprocessable Entity` - Ошибка валидации файла

### 11. Удалить изображение продукта

**DELETE** `/api/products/images/{image_id}`

Удаляет изображение продукта. Требует права администратора.

#### Запрос
```http
DELETE /api/products/images/image-uuid-123
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Изображение не найдено

## Управление категориями продуктов

### 12. Добавить продукт в категорию

**POST** `/api/products/{product_id}/categories`

Добавляет продукт в категорию. Требует права администратора.

#### Запрос
```http
POST /api/products/psih-basic-tshirt/categories
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "category_id": "category-uuid-123"
}
```

**Обязательные поля:**
- `category_id` (string) - ID категории

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт или категория не найдены
- `422 Unprocessable Entity` - Ошибка валидации данных

### 13. Удалить продукт из категории

**DELETE** `/api/products/{product_id}/categories/{category_id}`

Удаляет продукт из категории. Требует права администратора.

#### Запрос
```http
DELETE /api/products/psih-basic-tshirt/categories/category-uuid-123
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт, категория или связь не найдены

## Управление коллекциями продуктов

### 14. Добавить продукт в коллекцию

**POST** `/api/products/{product_id}/collections`

Добавляет продукт в коллекцию. Требует права администратора.

#### Запрос
```http
POST /api/products/psih-basic-tshirt/collections
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "collection_id": "spring-26",
  "sort_order": 1
}
```

**Обязательные поля:**
- `collection_id` (string) - ID коллекции

**Необязательные поля:**
- `sort_order` (integer) - Порядок сортировки в коллекции (по умолчанию 0)

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт или коллекция не найдены
- `422 Unprocessable Entity` - Ошибка валидации данных

### 15. Удалить продукт из коллекции

**DELETE** `/api/products/{product_id}/collections/{collection_id}`

Удаляет продукт из коллекции. Требует права администратора.

#### Запрос
```http
DELETE /api/products/psih-basic-tshirt/collections/spring-26
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Продукт, коллекция или связь не найдены

## Коды ошибок

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | Успех | - |
| 201 | Создано | - |
| 204 | Успешно, без содержимого | - |
| 400 | Неверный запрос | Проверить данные |
| 403 | Доступ запрещен | Проверить права администратора |
| 404 | Не найдено | Проверить ID |
| 422 | Ошибка валидации | Проверить формат данных |

## Особенности

1. **Аутентификация**: Все эндпоинты требуют JWT токен в заголовке `Authorization: Bearer your_token`
2. **Права доступа**: Все эндпоинты требуют права администратора (`is_admin: true`)
3. **Изображения**: При загрузке автоматически создаются три версии (оригинал, medium, small)
4. **Каскадное удаление**: При удалении продукта удаляются все связанные цвета, размеры и изображения
5. **Уникальность**: ID и slug продуктов должны быть уникальными
6. **Валидация**: Все поля проходят валидацию по длине и формату

## Swagger UI

Для тестирования API доступна интерактивная документация:
- **URL**: `http://localhost:8000/docs`
- **Раздел**: Products
- **Авторизация**: Используйте кнопку "Authorize" для добавления JWT токена
