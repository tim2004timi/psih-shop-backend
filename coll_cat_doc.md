# Документация по эндпоинтам коллекций и категорий

## Обзор

Документация для всех эндпоинтов коллекций и категорий, включая GET, POST, PUT, DELETE операции.

**Базовый URL:** `http://localhost:8000/api`

## Коллекции (Collections)

### 1. Получить список коллекций

**GET** `/api/collections`

Получает список всех коллекций с изображениями и пагинацией.

#### Запрос
```http
GET /api/collections?skip=0&limit=20
```

**Параметры:**
- `skip` (integer, optional) - Количество записей для пропуска (по умолчанию 0, минимум 0)
- `limit` (integer, optional) - Количество записей для возврата (по умолчанию 100, минимум 1, максимум 1000)

#### Ответ
```json
{
  "collections": [
    {
      "id": "spring-26",
      "name": "Spring 2026",
      "slug": "spring-26",
      "season": "Spring",
      "year": 2026,
      "description": "Новая весенняя коллекция",
      "story": "История создания коллекции",
      "inspiration": "Вдохновение для коллекции",
      "key_pieces": ["tshirt", "dress", "jacket"],
      "sustainability": "Экологичные материалы",
      "is_new": true,
      "is_featured": false,
      "category": "unisex",
      "created_at": "2024-01-01T00:00:00",
      "images": [
        {
          "id": "image-uuid-1",
          "file": "http://localhost:9000/photos/uuid-123.jpg",
          "sort_order": 0
        }
      ]
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 20
}
```

### 2. Получить коллекцию по ID

**GET** `/api/collections/{collection_id}`

Получает информацию о коллекции по ID с изображениями.

#### Запрос
```http
GET /api/collections/spring-26
```

#### Ответ
```json
{
  "id": "spring-26",
  "name": "Spring 2026",
  "slug": "spring-26",
  "season": "Spring",
  "year": 2026,
  "description": "Новая весенняя коллекция",
  "story": "История создания коллекции",
  "inspiration": "Вдохновение для коллекции",
  "key_pieces": ["tshirt", "dress", "jacket"],
  "sustainability": "Экологичные материалы",
  "is_new": true,
  "is_featured": false,
  "category": "unisex",
  "created_at": "2024-01-01T00:00:00",
  "images": [
    {
      "id": "image-uuid-1",
      "file": "http://localhost:9000/photos/uuid-123.jpg",
      "sort_order": 0
    }
  ]
}
```

#### Ошибки
- `404 Not Found` - Коллекция не найдена

### 3. Получить продукты коллекции

**GET** `/api/collections/{collection_id}/products`

Получает все продукты, принадлежащие коллекции.

#### Запрос
```http
GET /api/collections/spring-26/products
```

#### Ответ
```json
[
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
    "description": "Классическая футболка",
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
      "care": "Machine wash cold",
      "shipping": "2-4 days",
      "returns": "14 days"
    },
    "status": "in_stock"
  }
]
```

### 4. Создать коллекцию

**POST** `/api/collections`

Создает новую коллекцию. Требует права администратора.

#### Запрос
```http
POST /api/collections
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "id": "summer-26",
  "name": "Summer 2026",
  "slug": "summer-26",
  "season": "Summer",
  "year": 2026,
  "description": "Летняя коллекция",
  "story": "История летней коллекции",
  "inspiration": "Летнее вдохновение",
  "key_pieces": ["shorts", "tank-top", "sandals"],
  "sustainability": "Экологичные материалы",
  "is_new": true,
  "is_featured": true,
  "category": "unisex"
}
```

**Обязательные поля:**
- `id` (string, max 50) - Уникальный ID коллекции
- `name` (string, max 100) - Название коллекции
- `slug` (string, max 100) - Уникальный slug для URL
- `season` (string, max 20) - Сезон коллекции
- `year` (integer) - Год коллекции

**Необязательные поля:**
- `description` (string) - Описание коллекции
- `story` (string) - История коллекции
- `inspiration` (string) - Вдохновение
- `key_pieces` (array of strings) - Ключевые изделия
- `sustainability` (string) - Информация об устойчивости
- `is_new` (boolean) - Новая коллекция (по умолчанию true)
- `is_featured` (boolean) - Рекомендуемая коллекция (по умолчанию false)
- `category` (enum) - Категория: "men", "women", "unisex" (по умолчанию "unisex")

#### Ответ
```json
{
  "id": "summer-26",
  "name": "Summer 2026",
  "slug": "summer-26",
  "season": "Summer",
  "year": 2026,
  "description": "Летняя коллекция",
  "story": "История летней коллекции",
  "inspiration": "Летнее вдохновение",
  "key_pieces": ["shorts", "tank-top", "sandals"],
  "sustainability": "Экологичные материалы",
  "is_new": true,
  "is_featured": true,
  "category": "unisex",
  "created_at": "2024-01-01T00:00:00",
  "images": []
}
```

#### Ошибки
- `400 Bad Request` - Коллекция с таким ID уже существует
- `403 Forbidden` - Требуются права администратора
- `422 Unprocessable Entity` - Ошибка валидации данных

### 5. Обновить коллекцию

**PUT** `/api/collections/{collection_id}`

Обновляет информацию о коллекции. Требует права администратора.

#### Запрос
```http
PUT /api/collections/summer-26
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "name": "Summer 2026 Updated",
  "description": "Обновленное описание летней коллекции",
  "is_featured": false
}
```

**Все поля необязательные:**
- `name` (string, max 100) - Новое название
- `slug` (string, max 100) - Новый slug
- `season` (string, max 20) - Новый сезон
- `year` (integer) - Новый год
- `description` (string) - Новое описание
- `story` (string) - Новая история
- `inspiration` (string) - Новое вдохновение
- `key_pieces` (array of strings) - Новые ключевые изделия
- `sustainability` (string) - Новая информация об устойчивости
- `is_new` (boolean) - Новый статус
- `is_featured` (boolean) - Новый статус рекомендации
- `category` (enum) - Новая категория

#### Ответ
```json
{
  "id": "summer-26",
  "name": "Summer 2026 Updated",
  "slug": "summer-26",
  "season": "Summer",
  "year": 2026,
  "description": "Обновленное описание летней коллекции",
  "story": "История летней коллекции",
  "inspiration": "Летнее вдохновение",
  "key_pieces": ["shorts", "tank-top", "sandals"],
  "sustainability": "Экологичные материалы",
  "is_new": true,
  "is_featured": false,
  "category": "unisex",
  "created_at": "2024-01-01T00:00:00",
  "images": [
    {
      "id": "image-uuid-1",
      "file": "http://localhost:9000/photos/uuid-123.jpg",
      "sort_order": 0
    }
  ]
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Коллекция не найдена
- `422 Unprocessable Entity` - Ошибка валидации данных

### 6. Удалить коллекцию

**DELETE** `/api/collections/{collection_id}`

Удаляет коллекцию. Требует права администратора.

#### Запрос
```http
DELETE /api/collections/summer-26
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Коллекция не найдена

### 7. Добавить изображение в коллекцию

**POST** `/api/collections/{collection_id}/images`

Добавляет изображение в коллекцию. Требует права администратора.

#### Запрос
```http
POST /api/collections/summer-26/images
Authorization: Bearer your_jwt_token
Content-Type: multipart/form-data

file: [binary image data]
```

**Параметры:**
- `file` (file, required) - Файл изображения

#### Ответ
```json
{
  "id": "image-uuid-123",
  "file": "http://localhost:9000/photos/uuid-123.jpg"
}
```

**Примечание:** При загрузке изображения автоматически создаются три версии:
- Оригинал: `uuid.jpg`
- Medium: `uuid-medium.jpg`
- Small: `uuid-small.jpg`

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Коллекция не найдена
- `422 Unprocessable Entity` - Ошибка валидации файла

### 8. Удалить изображение коллекции

**DELETE** `/api/collections/images/{image_id}`

Удаляет изображение коллекции. Требует права администратора.

#### Запрос
```http
DELETE /api/collections/images/image-uuid-123
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Изображение не найдено

## Категории (Categories)

### 9. Получить дерево категорий

**GET** `/api/categories`

Получает иерархическое дерево всех категорий.

#### Запрос
```http
GET /api/categories
```

#### Ответ
```json
[
  {
    "id": "men",
    "name": "Men",
    "slug": "men",
    "children": [
      {
        "id": "men-shirts",
        "name": "Shirts",
        "slug": "shirts",
        "children": []
      },
      {
        "id": "men-outerwear",
        "name": "Outerwear",
        "slug": "outerwear",
        "children": []
      }
    ]
  },
  {
    "id": "women",
    "name": "Women",
    "slug": "women",
    "children": [
      {
        "id": "women-dresses",
        "name": "Dresses",
        "slug": "dresses",
        "children": []
      }
    ]
  }
]
```

### 10. Получить продукты по категории

**GET** `/api/categories/{slug}`

Получает все продукты, принадлежащие категории по slug.

#### Запрос
```http
GET /api/categories/shirts
```

#### Ответ
```json
[
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
    "description": "Классическая футболка",
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
      "care": "Machine wash cold",
      "shipping": "2-4 days",
      "returns": "14 days"
    },
    "status": "in_stock"
  }
]
```

#### Ошибки
- `404 Not Found` - Категория не найдена

### 11. Создать категорию

**POST** `/api/categories`

Создает новую категорию. Требует права администратора.

#### Запрос
```http
POST /api/categories
Authorization: Bearer your_jwt_token
Content-Type: application/json

{
  "id": "men-pants",
  "name": "Pants",
  "slug": "pants",
  "parent_id": "men",
  "level": 1,
  "sort_order": 2,
  "is_active": true
}
```

**Обязательные поля:**
- `id` (string) - Уникальный ID категории
- `name` (string) - Название категории
- `slug` (string) - Уникальный slug для URL

**Необязательные поля:**
- `parent_id` (string) - ID родительской категории
- `level` (integer) - Уровень в иерархии (по умолчанию 0)
- `sort_order` (integer) - Порядок сортировки (по умолчанию 0)
- `is_active` (boolean) - Активна ли категория (по умолчанию true)

#### Ответ
```json
{
  "id": "men-pants",
  "name": "Pants",
  "slug": "pants",
  "parent_id": "men",
  "level": 1,
  "sort_order": 2,
  "is_active": true
}
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `422 Unprocessable Entity` - Ошибка валидации данных

### 12. Удалить категорию

**DELETE** `/api/categories/{category_id}`

Удаляет категорию. Требует права администратора.

#### Запрос
```http
DELETE /api/categories/men-pants
Authorization: Bearer your_jwt_token
```

#### Ответ
```http
HTTP/1.1 204 No Content
```

#### Ошибки
- `403 Forbidden` - Требуются права администратора
- `404 Not Found` - Категория не найдена

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

1. **Аутентификация**: Все POST, PUT, DELETE эндпоинты требуют JWT токен в заголовке `Authorization: Bearer your_token`
2. **Права доступа**: Все модифицирующие операции требуют права администратора (`is_admin: true`)
3. **Изображения**: При загрузке автоматически создаются три версии (оригинал, medium, small)
4. **Каскадное удаление**: При удалении коллекции/категории удаляются все связанные данные
5. **Уникальность**: ID и slug коллекций/категорий должны быть уникальными
6. **Иерархия**: Категории поддерживают многоуровневую иерархию через parent_id
7. **Валидация**: Все поля проходят валидацию по длине и формату

## Swagger UI

Для тестирования API доступна интерактивная документация:
- **URL**: `http://localhost:8000/docs`
- **Разделы**: Collections, Categories
- **Авторизация**: Используйте кнопку "Authorize" для добавления JWT токена
