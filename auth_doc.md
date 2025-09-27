# Документация по аутентификации для фронтенда

## Обзор

API использует JWT (JSON Web Token) для аутентификации. Все защищенные эндпоинты требуют Bearer токен в заголовке `Authorization`.

**Базовый URL:** `http://localhost:8000/api`

## Эндпоинты аутентификации

### 1. Вход в систему (Login)

**POST** `/api/auth/token`

Получает JWT токен для аутентификации.

#### Запрос
```http
POST /api/auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

**Параметры:**
- `username` (string, required) - Email пользователя
- `password` (string, required) - Пароль пользователя

#### Ответ
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_admin": false
  }
}
```

#### Ошибки
- `401 Unauthorized` - Неверный email или пароль
- `422 Unprocessable Entity` - Неверный формат данных

### 2. Регистрация

**POST** `/api/auth/register`

Создает нового пользователя и возвращает токен.

#### Запрос
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "securepassword",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1234567890",
  "avatar": "https://example.com/avatar.jpg",
  "address": "123 Main St",
  "city": "Moscow",
  "postal_code": "123456",
  "country": "Russia"
}
```

**Поля:**
- `email` (string, required) - Email пользователя
- `password` (string, required) - Пароль
- `first_name` (string, required) - Имя
- `last_name` (string, required) - Фамилия
- `phone` (string, optional) - Телефон
- `avatar` (string, optional) - URL аватара
- `address` (string, optional) - Адрес
- `city` (string, optional) - Город
- `postal_code` (string, optional) - Почтовый индекс
- `country` (string, optional) - Страна (по умолчанию "Russia")

#### Ответ
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 2,
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "is_admin": false
  }
}
```

#### Ошибки
- `400 Bad Request` - Пользователь с таким email уже существует
- `422 Unprocessable Entity` - Неверный формат данных

### 3. Получить информацию о текущем пользователе

**GET** `/api/auth/me`

Возвращает полную информацию о текущем аутентифицированном пользователе.

#### Запрос
```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Ответ
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar": "https://example.com/avatar.jpg",
  "address": "123 Main St",
  "city": "Moscow",
  "postal_code": "123456",
  "country": "Russia",
  "is_admin": false,
  "is_active": true,
  "email_verified": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### Ошибки
- `401 Unauthorized` - Неверный или отсутствующий токен

## Управление пользователями

### 4. Обновить информацию о себе

**PUT** `/api/users/me`

Обновляет информацию о текущем пользователе.

#### Запрос
```http
PUT /api/users/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "first_name": "John Updated",
  "phone": "+9876543210",
  "city": "Saint Petersburg"
}
```

**Поля (все опциональные):**
- `first_name` (string) - Имя
- `last_name` (string) - Фамилия
- `phone` (string) - Телефон
- `avatar` (string) - URL аватара
- `address` (string) - Адрес
- `city` (string) - Город
- `postal_code` (string) - Почтовый индекс
- `country` (string) - Страна

#### Ответ
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John Updated",
  "last_name": "Doe",
  "phone": "+9876543210",
  "avatar": "https://example.com/avatar.jpg",
  "address": "123 Main St",
  "city": "Saint Petersburg",
  "postal_code": "123456",
  "country": "Russia",
  "is_admin": false,
  "is_active": true,
  "email_verified": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

### 5. Получить пользователя по ID

**GET** `/api/users/{user_id}`

Получает информацию о пользователе по ID. Доступно только самому пользователю или админу.

#### Запрос
```http
GET /api/users/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Ответ
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "avatar": "https://example.com/avatar.jpg",
  "address": "123 Main St",
  "city": "Moscow",
  "postal_code": "123456",
  "country": "Russia",
  "is_admin": false,
  "is_active": true,
  "email_verified": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### Ошибки
- `403 Forbidden` - Недостаточно прав
- `404 Not Found` - Пользователь не найден

## Админские функции

### 6. Получить список пользователей

**GET** `/api/users`

Получает список всех пользователей с пагинацией. Только для админов.

#### Запрос
```http
GET /api/users?skip=0&limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Параметры:**
- `skip` (integer, optional) - Количество записей для пропуска (по умолчанию 0)
- `limit` (integer, optional) - Количество записей для возврата (по умолчанию 100, максимум 1000)

#### Ответ
```json
[
  {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "avatar": "https://example.com/avatar.jpg",
    "address": "123 Main St",
    "city": "Moscow",
    "postal_code": "123456",
    "country": "Russia",
    "is_admin": false,
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### 7. Активировать пользователя

**PUT** `/api/users/{user_id}/activate`

Активирует пользователя. Только для админов.

#### Запрос
```http
PUT /api/users/1/activate
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 8. Деактивировать пользователя

**PUT** `/api/users/{user_id}/deactivate`

Деактивирует пользователя. Только для админов.

### 9. Удалить пользователя

**DELETE** `/api/users/{user_id}`

Удаляет пользователя. Только для админов.

#### Ответ
```json
{
  "message": "User deleted successfully"
}
```

### 10. Подтвердить email пользователя

**PUT** `/api/users/{user_id}/verify-email`

Подтверждает email пользователя. Доступно самому пользователю или админу.

### 11. Поиск пользователя по email

**GET** `/api/users/search/{email}`

Ищет пользователя по email. Только для админов.

#### Запрос
```http
GET /api/users/search/user@example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Использование токенов

### Добавление токена к запросам

Все защищенные эндпоинты требуют токен в заголовке `Authorization`:

```javascript
// JavaScript пример
const token = localStorage.getItem('access_token');
const response = await fetch('/api/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Обработка ошибок аутентификации

```javascript
// Проверка статуса ответа
if (response.status === 401) {
  // Токен недействителен или истек
  localStorage.removeItem('access_token');
  // Перенаправить на страницу входа
  window.location.href = '/login';
}
```

## Коды ошибок

| Код | Описание | Действие |
|-----|----------|----------|
| 200 | Успех | - |
| 201 | Создано | - |
| 400 | Неверный запрос | Проверить данные |
| 401 | Не авторизован | Войти в систему |
| 403 | Доступ запрещен | Проверить права |
| 404 | Не найдено | Проверить URL |
| 422 | Ошибка валидации | Проверить формат данных |

## Примеры использования

### React/JavaScript

```javascript
// Функция входа
async function login(email, password) {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch('/api/auth/token', {
    method: 'POST',
    body: formData
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data.user;
  } else {
    throw new Error('Login failed');
  }
}

// Функция получения текущего пользователя
async function getCurrentUser() {
  const token = localStorage.getItem('access_token');
  const response = await fetch('/api/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  if (response.ok) {
    return await response.json();
  } else {
    throw new Error('Failed to get user info');
  }
}

// Функция регистрации
async function register(userData) {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    return data.user;
  } else {
    const error = await response.json();
    throw new Error(error.detail);
  }
}
```

### Axios пример

```javascript
import axios from 'axios';

// Настройка axios с токеном
const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// Добавление токена к запросам
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Обработка ошибок аутентификации
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Использование
const login = async (email, password) => {
  const formData = new FormData();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await api.post('/auth/token', formData);
  localStorage.setItem('access_token', response.data.access_token);
  return response.data.user;
};
```

## Безопасность

1. **Хранение токенов**: Рекомендуется хранить токены в `httpOnly` cookies или в безопасном хранилище
2. **HTTPS**: В продакшене обязательно используйте HTTPS
3. **Время жизни токенов**: Токены имеют ограниченное время жизни (по умолчанию 60 минут)
4. **Обновление токенов**: Реализуйте механизм обновления токенов перед истечением

## Swagger UI

Для тестирования API доступна интерактивная документация:
- **URL**: `http://localhost:8000/docs`
- **Авторизация**: Используйте кнопку "Authorize" в правом верхнем углу
- **Токен**: Введите токен в формате `Bearer your_token_here`
