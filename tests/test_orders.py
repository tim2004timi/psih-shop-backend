"""
Тесты для эндпоинтов заказов
"""
import pytest
import httpx
import random
import string


@pytest.mark.asyncio
async def test_create_order_guest(client: httpx.AsyncClient):
    """Тест создания гостевого заказа (без аутентификации)"""
    # Сначала нужно получить существующий product_size_id
    # Для этого получаем список продуктов и находим размер
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_id = product["sizes"][0]["id"]
                
                response = await client.post(
                    "/api/orders",
                    json={
                        "order": {
                            "email": "guest@example.com",
                            "first_name": "Guest",
                            "last_name": "User",
                            "phone": "+1234567890",
                            "city": "Moscow",
                            "postal_code": "123456",
                            "address": "Test Address 123"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": 1
                            }
                        ]
                    }
                )
                # Может быть 201 (успех) или 400 (недостаточно товара)
                assert response.status_code in [201, 400]
                if response.status_code == 201:
                    data = response.json()
                    assert "id" in data
                    assert "email" in data
                    assert data["email"] == "guest@example.com"
                    assert "total_price" in data
                    assert "products" in data


@pytest.mark.asyncio
async def test_create_order_authenticated(client: httpx.AsyncClient, auth_token: str):
    """Тест создания заказа авторизованным пользователем"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    # Получаем существующий product_size_id
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_id = product["sizes"][0]["id"]
                
                headers = {"Authorization": f"Bearer {auth_token}"}
                response = await client.post(
                    "/api/orders",
                    headers=headers,
                    json={
                        "order": {
                            "email": "user@example.com",
                            "first_name": "Test",
                            "last_name": "User",
                            "phone": "+1234567890",
                            "city": "Moscow",
                            "postal_code": "123456",
                            "address": "Test Address 123"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": 1
                            }
                        ]
                    }
                )
                # Может быть 201 (успех) или 400 (недостаточно товара)
                assert response.status_code in [201, 400]
                if response.status_code == 201:
                    data = response.json()
                    assert "id" in data
                    assert "user_id" in data
                    assert data["user_id"] is not None  # Должен быть установлен автоматически


@pytest.mark.asyncio
async def test_create_order_insufficient_quantity(client: httpx.AsyncClient):
    """Тест создания заказа с недостаточным количеством товара"""
    # Получаем существующий product_size_id
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size = product["sizes"][0]
                size_id = size["id"]
                available_quantity = size.get("quantity", 0)
                
                # Пытаемся заказать больше, чем доступно
                response = await client.post(
                    "/api/orders",
                    json={
                        "order": {
                            "email": "test@example.com",
                            "first_name": "Test",
                            "last_name": "User"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": available_quantity + 100  # Заведомо больше доступного
                            }
                        ]
                    }
                )
                # Должна быть ошибка 400
                assert response.status_code == 400
                assert "Insufficient quantity" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_order_invalid_product_size(client: httpx.AsyncClient):
    """Тест создания заказа с несуществующим размером продукта"""
    response = await client.post(
        "/api/orders",
        json={
            "order": {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            },
            "products": [
                {
                    "product_size_id": 999999,  # Несуществующий ID
                    "quantity": 1
                }
            ]
        }
    )
    assert response.status_code == 404
    assert "Product sizes not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_order_empty_products(client: httpx.AsyncClient):
    """Тест создания заказа без товаров"""
    response = await client.post(
        "/api/orders",
        json={
            "order": {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            },
            "products": []
        }
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_orders_list(client: httpx.AsyncClient, auth_token: str):
    """Тест получения списка заказов"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/orders?skip=0&limit=10", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Если есть заказы, проверяем структуру
    if len(data) > 0:
        order = data[0]
        assert "id" in order
        assert "email" in order
        assert "total_price" in order
        assert "status" in order
        assert "products" in order


@pytest.mark.asyncio
async def test_get_orders_list_unauthorized(client: httpx.AsyncClient):
    """Тест получения списка заказов без аутентификации"""
    response = await client.get("/api/orders")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_order_by_id(client: httpx.AsyncClient, auth_token: str):
    """Тест получения заказа по ID"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Сначала создаем заказ, если возможно
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_id = product["sizes"][0]["id"]
                
                # Создаем заказ
                create_response = await client.post(
                    "/api/orders",
                    headers=headers,
                    json={
                        "order": {
                            "email": "user@example.com",
                            "first_name": "Test",
                            "last_name": "User"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": 1
                            }
                        ]
                    }
                )
                
                if create_response.status_code == 201:
                    order_id = create_response.json()["id"]
                    
                    # Получаем заказ по ID
                    response = await client.get(f"/api/orders/{order_id}", headers=headers)
                    assert response.status_code == 200
                    data = response.json()
                    assert data["id"] == order_id
                    assert "email" in data
                    assert "products" in data
                    assert isinstance(data["products"], list)


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(client: httpx.AsyncClient, auth_token: str):
    """Тест получения несуществующего заказа"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/orders/999999", headers=headers)
    assert response.status_code == 404
    assert "Order not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_order_by_id_unauthorized(client: httpx.AsyncClient):
    """Тест получения заказа без аутентификации"""
    response = await client.get("/api/orders/1")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_order_status(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления статуса заказа (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Сначала создаем заказ
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_id = product["sizes"][0]["id"]
                
                # Создаем заказ
                create_response = await client.post(
                    "/api/orders",
                    headers=headers,
                    json={
                        "order": {
                            "email": "user@example.com",
                            "first_name": "Test",
                            "last_name": "User"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": 1
                            }
                        ]
                    }
                )
                
                if create_response.status_code == 201:
                    order_id = create_response.json()["id"]
                    
                    # Обновляем статус заказа
                    update_response = await client.put(
                        f"/api/orders/{order_id}",
                        headers=headers,
                        json={
                            "status": "shipped"
                        }
                    )
                    # Может быть 200 (если админ) или 403 (если не админ)
                    assert update_response.status_code in [200, 403]
                    
                    if update_response.status_code == 200:
                        data = update_response.json()
                        assert data["status"] == "shipped"
                        assert data["id"] == order_id


@pytest.mark.asyncio
async def test_update_order_status_not_found(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления несуществующего заказа"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.put(
        "/api/orders/999999",
        headers=headers,
        json={
            "status": "shipped"
        }
    )
    # Может быть 404 (заказ не найден) или 403 (нет прав)
    assert response.status_code in [403, 404]


@pytest.mark.asyncio
async def test_update_order_unauthorized(client: httpx.AsyncClient):
    """Тест обновления заказа без аутентификации"""
    response = await client.put(
        "/api/orders/1",
        json={
            "status": "shipped"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_order_invalid_status(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления заказа с невалидным статусом"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Сначала создаем заказ
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products and len(products) > 0:
            product = products[0]
            if product.get("sizes") and len(product["sizes"]) > 0:
                size_id = product["sizes"][0]["id"]
                
                create_response = await client.post(
                    "/api/orders",
                    headers=headers,
                    json={
                        "order": {
                            "email": "user@example.com",
                            "first_name": "Test",
                            "last_name": "User"
                        },
                        "products": [
                            {
                                "product_size_id": size_id,
                                "quantity": 1
                            }
                        ]
                    }
                )
                
                if create_response.status_code == 201:
                    order_id = create_response.json()["id"]
                    
                    # Пытаемся обновить с невалидным статусом
                    update_response = await client.put(
                        f"/api/orders/{order_id}",
                        headers=headers,
                        json={
                            "status": "invalid_status"
                        }
                    )
                    # Должна быть ошибка валидации
                    assert update_response.status_code == 422

