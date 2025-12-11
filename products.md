# Документация API: Продукты

**Base URL:** `http://109.172.36.219:8000/api`

## Получение продуктов

### 1. Получить список продуктов

**URL:** `GET /products`

**Описание:** Получает список всех продуктов с пагинацией и фильтрацией. Возвращает список вариантов продуктов (ProductColor) с их данными.

**Входные данные (Query параметры):**
- `skip` (int, опционально, по умолчанию: 0) - Количество записей для пропуска
- `limit` (int, опционально, по умолчанию: 100, максимум: 1000) - Количество записей для возврата
- `status` (string, опционально) - Фильтр по статусу продукта: `in_stock`, `out_of_stock`, `discontinued`
- `search` (string, опционально) - Поиск по названию или описанию

**Выходные данные:**
```json
{
  "products": [
    {
      "id": 1,
      "slug": "basic-tshirt-red",
      "title": "Basic T-Shirt",
      "categoryPath": [],
      "price": "29.99",
      "discount_price": "24.99",
      "currency": "EUR",
      "label": "Red",
      "hex": "#FF0000",
      "sizes": [
        {
          "size": "S",
          "quantity": 10
        },
        {
          "size": "M",
          "quantity": 15
        }
      ],
      "composition": "100% Cotton",
      "fit": "Regular",
      "description": "Comfortable basic t-shirt",
      "images": [
        {
          "file": "http://localhost:9000/photos/uuid.png",
          "alt": null,
          "w": null,
          "h": null,
          "color": null
        }
      ],
      "meta": {
        "care": "Machine wash",
        "shipping": "Free shipping",
        "returns": "30 days return"
      },
      "status": "in_stock"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 100
}
```

### 2. Получить продукт по ID

**URL:** `GET /products/{product_color_id}`

**Описание:** Получает информацию о продукте по ID цвета продукта (product_color_id).

**Входные данные (Path параметры):**
- `product_color_id` (int, обязательно) - ID цвета продукта

**Выходные данные:**
```json
{
  "id": 1,
  "slug": "basic-tshirt-red",
  "title": "Basic T-Shirt",
  "categoryPath": [],
  "price": "29.99",
  "discount_price": "24.99",
  "currency": "EUR",
  "label": "Red",
  "hex": "#FF0000",
  "sizes": [
    {
      "size": "S",
      "quantity": 10
    },
    {
      "size": "M",
      "quantity": 15
    }
  ],
  "composition": "100% Cotton",
  "fit": "Regular",
  "description": "Comfortable basic t-shirt",
  "images": [
    {
      "file": "http://localhost:9000/photos/uuid.png",
      "alt": null,
      "w": null,
      "h": null,
      "color": null
    }
  ],
  "meta": {
    "care": "Machine wash",
    "shipping": "Free shipping",
    "returns": "30 days return"
  },
  "status": "in_stock"
}
```

### 3. Получить продукт по slug

**URL:** `GET /products/slug/{slug}`

**Описание:** Получает информацию о продукте по его slug.

**Входные данные (Path параметры):**
- `slug` (string, обязательно) - Slug продукта

**Выходные данные:**
```json
{
  "id": 1,
  "slug": "basic-tshirt-red",
  "title": "Basic T-Shirt",
  "categoryPath": [],
  "price": "29.99",
  "discount_price": "24.99",
  "currency": "EUR",
  "label": "Red",
  "hex": "#FF0000",
  "sizes": [
    {
      "size": "S",
      "quantity": 10
    }
  ],
  "composition": "100% Cotton",
  "fit": "Regular",
  "description": "Comfortable basic t-shirt",
  "images": [
    {
      "file": "http://localhost:9000/photos/uuid.png",
      "alt": null,
      "w": null,
      "h": null,
      "color": null
    }
  ],
  "meta": {
    "care": "Machine wash",
    "shipping": "Free shipping",
    "returns": "30 days return"
  },
  "status": "in_stock"
}
```

## Управление базовыми продуктами

### 4. Создать новый продукт

**URL:** `POST /products`

**Описание:** Создает новый базовый продукт. Требует права администратора. После создания продукта необходимо создать цветовую вариацию (ProductColor).

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (JSON):**
```json
{
  "description": "Comfortable basic t-shirt",
  "price": "29.99",
  "discount_price": "24.99",
  "currency": "EUR",
  "composition": "100% Cotton",
  "fit": "Regular",
  "status": "in_stock",
  "is_pre_order": false,
  "meta_care": "Machine wash",
  "meta_shipping": "Free shipping",
  "meta_returns": "30 days return"
}
```

**Обязательные поля:**
- `price` (string, decimal) - Цена продукта

**Необязательные поля:**
- `description` (string) - Описание продукта
- `discount_price` (string, decimal) - Цена со скидкой
- `currency` (string, по умолчанию: "EUR") - Валюта
- `composition` (string, максимум 200 символов) - Состав продукта
- `fit` (string, максимум 50 символов) - Посадка/размер
- `status` (string, по умолчанию: "in_stock") - Статус: `in_stock`, `out_of_stock`, `discontinued`
- `is_pre_order` (boolean, по умолчанию: false) - Доступен ли для предзаказа
- `meta_care` (string, максимум 200 символов) - Инструкции по уходу
- `meta_shipping` (string, максимум 100 символов) - Информация о доставке
- `meta_returns` (string, максимум 100 символов) - Информация о возврате

**Выходные данные:**
```json
{
  "id": 1,
  "message": "Product created. Now create a color variant."
}
```

### 5. Обновить базовый продукт

**URL:** `PUT /products/base/{product_id}`

**Описание:** Обновляет информацию о базовом продукте. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Входные данные (JSON):**
```json
{
  "description": "Updated description",
  "price": "34.99",
  "discount_price": "29.99",
  "currency": "EUR",
  "composition": "100% Organic Cotton",
  "fit": "Slim",
  "status": "in_stock",
  "is_pre_order": false,
  "meta_care": "Hand wash only",
  "meta_shipping": "Express shipping available",
  "meta_returns": "14 days return"
}
```

**Все поля необязательные** (обновляются только переданные поля)

**Выходные данные:**
```json
{
  "id": 1,
  "message": "Product updated"
}
```

### 6. Удалить продукт

**URL:** `DELETE /products/base/{product_id}`

**Описание:** Удаляет базовый продукт и все связанные данные (цвета, размеры, изображения). Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Выходные данные:**
```json
{
  "message": "Product deleted successfully"
}
```

## Управление цветами продуктов

### 7. Получить список цветов продукта

**URL:** `GET /products/{product_id}/colors`

**Описание:** Получает список всех цветовых вариаций для указанного базового продукта.

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Выходные данные:**
```json
[
  {
    "id": 1,
    "slug": "basic-tshirt-red",
    "title": "Basic T-Shirt",
    "label": "Red",
    "hex": "#FF0000"
  },
  {
    "id": 2,
    "slug": "basic-tshirt-blue",
    "title": "Basic T-Shirt",
    "label": "Blue",
    "hex": "#0000FF"
  }
]
```

### 8. Добавить цвет продукта

**URL:** `POST /products/{product_id}/colors`

**Описание:** Создает новую цветовую вариацию продукта. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Входные данные (JSON):**
```json
{
  "slug": "basic-tshirt-red",
  "title": "Basic T-Shirt",
  "label": "Red",
  "hex": "#FF0000"
}
```

**Обязательные поля:**
- `slug` (string, максимум 100 символов) - Уникальный slug для продукта с цветом
- `title` (string, максимум 200 символов) - Название продукта
- `label` (string, максимум 100 символов) - Название цвета
- `hex` (string, максимум 7 символов) - HEX код цвета

**Выходные данные:**
```json
{
  "id": 1,
  "slug": "basic-tshirt-red",
  "title": "Basic T-Shirt",
  "label": "Red",
  "hex": "#FF0000"
}
```

### 9. Обновить цвет продукта

**URL:** `PUT /products/colors/{color_id}`

**Описание:** Обновляет информацию о цветовой вариации продукта. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `color_id` (int, обязательно) - ID цвета продукта

**Входные данные (JSON):**
```json
{
  "slug": "basic-tshirt-crimson",
  "title": "Basic T-Shirt Updated",
  "label": "Crimson Red",
  "hex": "#DC143C"
}
```

**Все поля необязательные** (обновляются только переданные поля)

**Выходные данные:**
```json
{
  "id": 1,
  "slug": "basic-tshirt-crimson",
  "title": "Basic T-Shirt Updated",
  "label": "Crimson Red",
  "hex": "#DC143C"
}
```

### 10. Удалить цвет продукта

**URL:** `DELETE /products/colors/{color_id}`

**Описание:** Удаляет цветовую вариацию продукта и все связанные данные (размеры, изображения). Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `color_id` (int, обязательно) - ID цвета продукта

**Выходные данные:**
```
HTTP 204 No Content
```

## Управление изображениями продуктов

### 11. Получить список изображений продукта

**URL:** `GET /products/colors/{product_color_id}/images`

**Описание:** Получает список всех изображений для указанной цветовой вариации продукта, отсортированных по sort_order.

**Входные данные (Path параметры):**
- `product_color_id` (int, обязательно) - ID цвета продукта

**Выходные данные:**
```json
[
  {
    "id": 1,
    "file": "http://localhost:9000/photos/uuid.png",
    "sort_order": 0
  },
  {
    "id": 2,
    "file": "http://localhost:9000/photos/uuid2.png",
    "sort_order": 1
  }
]
```

### 12. Загрузить изображение продукта

**URL:** `POST /products/colors/{product_color_id}/images`

**Описание:** Загружает изображение для цветовой вариации продукта. Автоматически создает две копии (medium и small) для оптимизации. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_color_id` (int, обязательно) - ID цвета продукта

**Входные данные (Form data):**
- `file` (file, обязательно) - Файл изображения
- `sort_order` (int, опционально, по умолчанию: 0) - Порядок сортировки изображения

**Выходные данные:**
```json
{
  "id": 1,
  "file": "http://localhost:9000/photos/uuid.png",
  "sort_order": 0
}
```

### 13. Удалить изображение продукта

**URL:** `DELETE /products/images/{image_id}`

**Описание:** Удаляет изображение продукта. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `image_id` (int, обязательно) - ID изображения

**Выходные данные:**
```
HTTP 204 No Content
```

## Управление размерами продуктов

### 14. Получить список размеров продукта

**URL:** `GET /products/colors/{product_color_id}/sizes`

**Описание:** Получает список всех размеров с количеством для указанной цветовой вариации продукта.

**Входные данные (Path параметры):**
- `product_color_id` (int, обязательно) - ID цвета продукта

**Выходные данные:**
```json
[
  {
    "id": 1,
    "size": "S",
    "quantity": 10
  },
  {
    "id": 2,
    "size": "M",
    "quantity": 15
  },
  {
    "id": 3,
    "size": "L",
    "quantity": 8
  }
]
```

### 15. Добавить размер продукта

**URL:** `POST /products/colors/{product_color_id}/sizes`

**Описание:** Добавляет размер с количеством для цветовой вариации продукта. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_color_id` (int, обязательно) - ID цвета продукта

**Входные данные (JSON):**
```json
{
  "size": "XL",
  "quantity": 5
}
```

**Обязательные поля:**
- `size` (string, максимум 10 символов) - Размер

**Необязательные поля:**
- `quantity` (int, по умолчанию: 0, минимум: 0) - Количество товара данного размера

**Выходные данные:**
```json
{
  "id": 4,
  "size": "XL",
  "quantity": 5
}
```

### 16. Обновить размер продукта

**URL:** `PUT /products/sizes/{size_id}`

**Описание:** Обновляет размер или количество товара. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `size_id` (int, обязательно) - ID размера

**Входные данные (Query параметры или JSON):**
- `size` (string, опционально) - Новый размер
- `quantity` (int, опционально, минимум: 0) - Новое количество

**Пример запроса:**
```
PUT /products/sizes/1?size=M&quantity=20
```

или

```json
{
  "size": "M",
  "quantity": 20
}
```

**Выходные данные:**
```json
{
  "id": 1,
  "size": "M",
  "quantity": 20
}
```

### 17. Удалить размер продукта

**URL:** `DELETE /products/sizes/{size_id}`

**Описание:** Удаляет размер продукта. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `size_id` (int, обязательно) - ID размера

**Выходные данные:**
```
HTTP 204 No Content
```

## Управление категориями продуктов

### 18. Добавить продукт в категорию

**URL:** `POST /products/base/{product_id}/categories`

**Описание:** Добавляет базовый продукт в категорию. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Входные данные (JSON):**
```json
{
  "category_id": 1
}
```

**Обязательные поля:**
- `category_id` (int) - ID категории

**Выходные данные:**
```
HTTP 204 No Content
```

### 19. Удалить продукт из категории

**URL:** `DELETE /products/base/{product_id}/categories/{category_id}`

**Описание:** Удаляет базовый продукт из категории. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта
- `category_id` (int, обязательно) - ID категории

**Выходные данные:**
```
HTTP 204 No Content
```

## Управление коллекциями продуктов

### 20. Добавить продукт в коллекцию

**URL:** `POST /products/base/{product_id}/collections`

**Описание:** Добавляет базовый продукт в коллекцию с указанным порядком сортировки. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Входные данные (JSON):**
```json
{
  "collection_id": 1,
  "sort_order": 0
}
```

**Обязательные поля:**
- `collection_id` (int) - ID коллекции

**Необязательные поля:**
- `sort_order` (int, по умолчанию: 0) - Порядок сортировки продукта в коллекции

**Выходные данные:**
```
HTTP 204 No Content
```

### 21. Удалить продукт из коллекции

**URL:** `DELETE /products/base/{product_id}/collections/{collection_id}`

**Описание:** Удаляет базовый продукт из коллекции. Требует права администратора.

**Аутентификация:** Требуется (Bearer token, права администратора)

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта
- `collection_id` (int, обязательно) - ID коллекции

**Выходные данные:**
```
HTTP 204 No Content
```

