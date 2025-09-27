# Документация по GET эндпоинтам продуктов для фронтенда

## Обзор

API предоставляет несколько GET эндпоинтов для получения информации о продуктах, их цветах, размерах и изображениях.

**Базовый URL:** `http://localhost:8000/api`

## Основные GET эндпоинты продуктов

### 1. Получить список продуктов

**GET** `/api/products`

Получает список всех продуктов с пагинацией и фильтрацией.

#### Запрос
```http
GET /api/products?skip=0&limit=20&status=in_stock&search=tshirt
```

**Параметры запроса:**
- `skip` (integer, optional) - Количество записей для пропуска (по умолчанию 0, минимум 0)
- `limit` (integer, optional) - Количество записей для возврата (по умолчанию 100, минимум 1, максимум 1000)
- `status` (string, optional) - Фильтр по статусу продукта (`in_stock`, `out_of_stock`, `discontinued`)
- `search` (string, optional) - Поиск по названию или описанию продукта

#### Ответ
```json
{
  "products": [
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
        },
        {
          "code": "black",
          "label": "Black",
          "hex": "#000000"
        }
      ],
      "sizes": ["S", "M", "L", "XL"],
      "composition": "100% cotton",
      "fit": "regular",
      "description": "Классическая футболка из мягкого хлопка",
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
  ],
  "total": 50,
  "skip": 0,
  "limit": 20
}
```

#### Примеры запросов
```javascript
// Получить первые 20 продуктов
GET /api/products?limit=20

// Получить продукты со статусом "в наличии"
GET /api/products?status=in_stock

// Поиск по названию
GET /api/products?search=tshirt

// Пагинация
GET /api/products?skip=20&limit=20

// Комбинированный запрос
GET /api/products?status=in_stock&search=basic&skip=0&limit=10
```

### 2. Получить продукт по ID

**GET** `/api/products/{product_id}`

Получает полную информацию о продукте по его ID.

#### Запрос
```http
GET /api/products/psih-basic-tshirt
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
    },
    {
      "code": "black",
      "label": "Black",
      "hex": "#000000"
    }
  ],
  "sizes": ["S", "M", "L", "XL"],
  "composition": "100% cotton",
  "fit": "regular",
  "description": "Классическая футболка из мягкого хлопка",
  "images": [
    {
      "file": "http://localhost:9000/photos/uuid-123.jpg",
      "alt": null,
      "w": null,
      "h": null,
      "color": null
    },
    {
      "file": "http://localhost:9000/photos/uuid-124.jpg",
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
```

#### Ошибки
- `404 Not Found` - Продукт не найден

### 3. Получить продукт по slug

**GET** `/api/products/slug/{slug}`

Получает полную информацию о продукте по его slug (человекочитаемый URL).

#### Запрос
```http
GET /api/products/slug/basic-tshirt
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
```

#### Ошибки
- `404 Not Found` - Продукт не найден

## Эндпоинты для цветов продуктов

### 4. Получить цвета продукта

**GET** `/api/products/{product_id}/colors`

Получает список всех цветов для конкретного продукта.

#### Запрос
```http
GET /api/products/psih-basic-tshirt/colors
```

#### Ответ
```json
[
  {
    "id": "color-uuid-1",
    "code": "white",
    "label": "White",
    "hex": "#FFFFFF"
  },
  {
    "id": "color-uuid-2",
    "code": "black",
    "label": "Black",
    "hex": "#000000"
  },
  {
    "id": "color-uuid-3",
    "code": "navy",
    "label": "Navy Blue",
    "hex": "#1B365D"
  }
]
```

## Эндпоинты для размеров продуктов

### 5. Получить размеры продукта

**GET** `/api/products/{product_id}/sizes`

Получает список всех размеров для конкретного продукта.

#### Запрос
```http
GET /api/products/psih-basic-tshirt/sizes
```

#### Ответ
```json
[
  {
    "id": "size-uuid-1",
    "size": "S"
  },
  {
    "id": "size-uuid-2",
    "size": "M"
  },
  {
    "id": "size-uuid-3",
    "size": "L"
  },
  {
    "id": "size-uuid-4",
    "size": "XL"
  }
]
```

## Эндпоинты для изображений продуктов

### 6. Получить изображения продукта

**GET** `/api/products/{product_id}/images`

Получает список всех изображений для конкретного продукта.

#### Запрос
```http
GET /api/products/psih-basic-tshirt/images
```

#### Ответ
```json
[
  {
    "id": "image-uuid-1",
    "file": "http://localhost:9000/photos/uuid-123.jpg",
    "sort_order": 0
  },
  {
    "id": "image-uuid-2",
    "file": "http://localhost:9000/photos/uuid-124.jpg",
    "sort_order": 1
  },
  {
    "id": "image-uuid-3",
    "file": "http://localhost:9000/photos/uuid-125.jpg",
    "sort_order": 2
  }
]
```

## Структуры данных

### ProductPublic
Основная структура продукта, возвращаемая всеми GET эндпоинтами:

```typescript
interface ProductPublic {
  id: string;                    // Уникальный ID продукта
  slug: string;                  // Человекочитаемый URL
  title: string;                 // Название продукта
  categoryPath: string[];        // Путь по категориям (пока пустой массив)
  price: number;                // Цена
  currency: string;             // Валюта (по умолчанию "EUR")
  colors: ProductColorOut[];    // Массив цветов
  sizes: string[];              // Массив размеров
  composition?: string;         // Состав
  fit?: string;                 // Посадка
  description?: string;         // Описание
  images: ProductImageOut[];    // Массив изображений
  meta: ProductMeta;           // Мета-информация
  status: ProductStatus;        // Статус продукта
}
```

### ProductColorOut
```typescript
interface ProductColorOut {
  code: string;    // Код цвета (например, "white")
  label: string;   // Отображаемое название (например, "White")
  hex: string;     // HEX код цвета (например, "#FFFFFF")
}
```

### ProductImageOut
```typescript
interface ProductImageOut {
  file: string;           // URL изображения
  alt?: string;          // Альтернативный текст
  w?: number;            // Ширина
  h?: number;            // Высота
  color?: string;        // Цвет изображения
}
```

### ProductMeta
```typescript
interface ProductMeta {
  care?: string;         // Инструкции по уходу
  shipping?: string;     // Информация о доставке
  returns?: string;     // Информация о возврате
}
```

### ProductStatus
```typescript
enum ProductStatus {
  IN_STOCK = "in_stock",           // В наличии
  OUT_OF_STOCK = "out_of_stock",   // Нет в наличии
  DISCONTINUED = "discontinued"    // Снят с производства
}
```

### ProductList
```typescript
interface ProductList {
  products: ProductPublic[];  // Массив продуктов
  total: number;             // Общее количество
  skip: number;              // Пропущено записей
  limit: number;             // Лимит записей
}
```

## Примеры использования

### JavaScript/React

```javascript
// Получить список продуктов
async function getProducts(filters = {}) {
  const params = new URLSearchParams();
  
  if (filters.skip) params.append('skip', filters.skip);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.status) params.append('status', filters.status);
  if (filters.search) params.append('search', filters.search);
  
  const response = await fetch(`/api/products?${params}`);
  return await response.json();
}

// Получить продукт по ID
async function getProductById(productId) {
  const response = await fetch(`/api/products/${productId}`);
  if (response.ok) {
    return await response.json();
  } else {
    throw new Error('Product not found');
  }
}

// Получить продукт по slug
async function getProductBySlug(slug) {
  const response = await fetch(`/api/products/slug/${slug}`);
  if (response.ok) {
    return await response.json();
  } else {
    throw new Error('Product not found');
  }
}

// Получить цвета продукта
async function getProductColors(productId) {
  const response = await fetch(`/api/products/${productId}/colors`);
  return await response.json();
}

// Получить размеры продукта
async function getProductSizes(productId) {
  const response = await fetch(`/api/products/${productId}/sizes`);
  return await response.json();
}

// Получить изображения продукта
async function getProductImages(productId) {
  const response = await fetch(`/api/products/${productId}/images`);
  return await response.json();
}
```

### Axios пример

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// Получить список продуктов с фильтрацией
const getProducts = async (params = {}) => {
  const response = await api.get('/products', { params });
  return response.data;
};

// Получить продукт по ID
const getProductById = async (productId) => {
  const response = await api.get(`/products/${productId}`);
  return response.data;
};

// Получить продукт по slug
const getProductBySlug = async (slug) => {
  const response = await api.get(`/products/slug/${slug}`);
  return response.data;
};

// Получить цвета продукта
const getProductColors = async (productId) => {
  const response = await api.get(`/products/${productId}/colors`);
  return response.data;
};

// Получить размеры продукта
const getProductSizes = async (productId) => {
  const response = await api.get(`/products/${productId}/sizes`);
  return response.data;
};

// Получить изображения продукта
const getProductImages = async (productId) => {
  const response = await api.get(`/products/${productId}/images`);
  return response.data;
};
```

### React Hook пример

```javascript
import { useState, useEffect } from 'react';

// Хук для получения списка продуктов
function useProducts(filters = {}) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({});

  useEffect(() => {
    async function fetchProducts() {
      try {
        setLoading(true);
        const params = new URLSearchParams();
        
        if (filters.skip) params.append('skip', filters.skip);
        if (filters.limit) params.append('limit', filters.limit);
        if (filters.status) params.append('status', filters.status);
        if (filters.search) params.append('search', filters.search);
        
        const response = await fetch(`/api/products?${params}`);
        const data = await response.json();
        
        setProducts(data.products);
        setPagination({
          total: data.total,
          skip: data.skip,
          limit: data.limit
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchProducts();
  }, [filters]);

  return { products, loading, error, pagination };
}

// Хук для получения одного продукта
function useProduct(productId) {
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchProduct() {
      try {
        setLoading(true);
        const response = await fetch(`/api/products/${productId}`);
        
        if (response.ok) {
          const data = await response.json();
          setProduct(data);
        } else {
          setError('Product not found');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (productId) {
      fetchProduct();
    }
  }, [productId]);

  return { product, loading, error };
}
```

## Коды ошибок

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | Успех | - |
| 404 | Продукт не найден | Проверить ID/slug |
| 422 | Ошибка валидации | Проверить параметры запроса |

## Особенности

1. **Пагинация**: Все списки поддерживают пагинацию через параметры `skip` и `limit`
2. **Фильтрация**: Список продуктов можно фильтровать по статусу и искать по названию/описанию
3. **Изображения**: Изображения хранятся в MinIO и автоматически генерируются в трех размерах (оригинал, medium, small)
4. **Цвета и размеры**: Возвращаются отдельными эндпоинтами для оптимизации
5. **Статусы**: Продукты могут иметь статус `in_stock`, `out_of_stock`, `discontinued`

## Swagger UI

Для тестирования API доступна интерактивная документация:
- **URL**: `http://localhost:8000/docs`
- **Раздел**: Products
- **Эндпоинты**: Все GET эндпоинты доступны для тестирования
