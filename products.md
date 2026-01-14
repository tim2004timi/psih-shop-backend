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
      "color_id": 5,
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
          "id": 1,
          "size": "S",
          "quantity": 10
        },
        {
          "id": 2,
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

**URL:** `GET /products/{product_id}`

**Описание:** Получает детальную информацию о продукте по его ID со всеми цветами, изображениями и размерами.

**Входные данные (Path параметры):**
- `product_id` (int, обязательно) - ID базового продукта

**Выходные данные:**
```json
{
  "id": 1,
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
  "meta_returns": "30 days return",
  "colors": [
    {
      "color_id": 1,
      "slug": "basic-tshirt-red",
      "title": "Basic T-Shirt",
      "label": "Red",
      "hex": "#FF0000"
    }
  ],
  "main_category": {
      "id": 10,
      "name": "Men",
      "slug": "men"
  }
}
```

### 3. Получить продукт по slug

**URL:** `GET /products/slug/{slug}`

**Описание:** Получает информацию о продукте по его slug. (Устаревший метод, рекомендуется использовать поиск с категорией).

**Входные данные (Path параметры):**
- `slug` (string, обязательно) - Slug продукта

### 4. Получить продукт по категории и slug

**URL:** `GET /products/{category_slug}/{slug}`

**Описание:** Получает информацию о продукте по его slug и slug категории. Это позволяет иметь товары с одинаковым slug в разных категориях.

**Входные данные (Path параметры):**
- `category_slug` (string, обязательно) - Slug категории
- `slug` (string, обязательно) - Slug продукта (цветового варианта)

**Выходные данные:**
Аналогично `GET /products/slug/{slug}`.

---

## Правила уникальности Slug

1. **Slug продукта больше не является глобально уникальным.**
2. **Уникальность в рамках категории:**
   - Slug должен быть уникальным среди всех товаров, привязанных к конкретной категории.
   - Один и тот же slug (например, "tovar") может существовать в категории "man" и в категории "woman".
   - Невозможно создать товар со slug "tovar" в категории "man", если там уже есть другой товар с таким slug.
   - Невозможно добавить товар со slug "tovar" в категорию "man", если там уже есть другой товар с таким slug.
3. **URL-адресация:**
   - Для доступа к товару рекомендуется использовать путь `/products/{category_slug}/{product_slug}`.
   - Старый эндпоинт `/products/slug/{slug}` сохранен для совместимости, но поведение при дублировании slug не гарантировано (вернет один из товаров).
