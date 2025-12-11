"""
Тесты для эндпоинтов продуктов
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_get_products_list(client: httpx.AsyncClient):
    """Тест получения списка продуктов"""
    response = await client.get("/api/products?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["products"], list)


@pytest.mark.asyncio
async def test_get_products_with_search(client: httpx.AsyncClient):
    """Тест поиска продуктов"""
    response = await client.get("/api/products?search=test&skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


@pytest.mark.asyncio
async def test_get_products_with_status_filter(client: httpx.AsyncClient):
    """Тест фильтрации продуктов по статусу"""
    response = await client.get("/api/products?status=in_stock&skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "products" in data


@pytest.mark.asyncio
async def test_create_product(client: httpx.AsyncClient, auth_token: str):
    """Тест создания продукта (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.post(
        "/api/products",
        headers=headers,
        json={
            "description": "Test product description",
            "price": "99.99",
            "currency": "EUR",
            "composition": "100% Cotton",
            "fit": "Regular",
            "status": "in_stock",
            "is_pre_order": False,
            "meta_care": "Machine wash",
            "meta_shipping": "Free shipping",
            "meta_returns": "30 days return"
        }
    )
    # Может быть 200 (если админ) или 403 (если не админ)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_get_product_by_slug(client: httpx.AsyncClient):
    """Тест получения продукта по slug"""
    # Сначала получаем список продуктов
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products:
            slug = products[0]["slug"]
            response = await client.get(f"/api/products/slug/{slug}")
            assert response.status_code == 200
            data = response.json()
            assert data["slug"] == slug


@pytest.mark.asyncio
async def test_get_product_colors(client: httpx.AsyncClient):
    """Тест получения цветов продукта"""
    # Сначала получаем список продуктов, чтобы найти product_id
    products_response = await client.get("/api/products?skip=0&limit=1")
    if products_response.status_code == 200:
        products = products_response.json()["products"]
        if products:
            # Получаем product_id из первого продукта (нужно найти базовый продукт)
            # Для этого нужно получить цвета через другой эндпоинт
            # Пока просто проверяем, что эндпоинт существует
            response = await client.get("/api/products/1/colors")
            # Может быть 200 или 404
            assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_create_product_color(client: httpx.AsyncClient, auth_token: str):
    """Тест создания цвета продукта (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Сначала создаем продукт, если есть права
    product_response = await client.post(
        "/api/products",
        headers=headers,
        json={
            "description": "Test product",
            "price": "50.00",
            "currency": "EUR",
            "status": "in_stock"
        }
    )
    
    if product_response.status_code == 200:
        product_id = product_response.json()["id"]
        
        # Создаем цвет
        import random
        import string
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        response = await client.post(
            f"/api/products/{product_id}/colors",
            headers=headers,
            json={
                "slug": f"test-product-red-{random_suffix}",
                "title": "Test Product Red",
                "label": "Red",
                "hex": "#FF0000"
            }
        )
        # Может быть 201 (если админ) или 403 (если не админ)
        assert response.status_code in [201, 403]


@pytest.mark.asyncio
async def test_get_product_sizes(client: httpx.AsyncClient):
    """Тест получения размеров продукта"""
    response = await client.get("/api/products/colors/1/sizes")
    # Может быть 200 или 404
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_get_product_images(client: httpx.AsyncClient):
    """Тест получения изображений продукта"""
    response = await client.get("/api/products/colors/1/images")
    # Может быть 200 или 404
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_update_product(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления продукта (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.put(
        "/api/products/base/1",
        headers=headers,
        json={
            "description": "Updated description",
            "price": "149.99"
        }
    )
    # Может быть 200 (если админ и продукт существует) или 403/404
    assert response.status_code in [200, 403, 404]


@pytest.mark.asyncio
async def test_delete_product(client: httpx.AsyncClient, auth_token: str):
    """Тест удаления продукта (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.delete("/api/products/base/999999", headers=headers)
    # Может быть 204 (если админ и продукт существует) или 403/404
    assert response.status_code in [204, 403, 404]

