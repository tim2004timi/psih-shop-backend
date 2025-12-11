"""
Тесты для эндпоинтов коллекций
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_get_collections_list(client: httpx.AsyncClient):
    """Тест получения списка коллекций"""
    response = await client.get("/api/collections?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "collections" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert isinstance(data["collections"], list)


@pytest.mark.asyncio
async def test_get_collection_by_id(client: httpx.AsyncClient):
    """Тест получения коллекции по ID"""
    # Сначала получаем список коллекций
    collections_response = await client.get("/api/collections?skip=0&limit=1")
    if collections_response.status_code == 200:
        collections = collections_response.json()["collections"]
        if collections:
            collection_id = collections[0]["id"]
            response = await client.get(f"/api/collections/{collection_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == collection_id
            assert "images" in data


@pytest.mark.asyncio
async def test_get_collection_products(client: httpx.AsyncClient):
    """Тест получения продуктов коллекции"""
    # Сначала получаем список коллекций
    collections_response = await client.get("/api/collections?skip=0&limit=1")
    if collections_response.status_code == 200:
        collections = collections_response.json()["collections"]
        if collections:
            collection_id = collections[0]["id"]
            response = await client.get(f"/api/collections/{collection_id}/products")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_collection(client: httpx.AsyncClient, auth_token: str):
    """Тест создания коллекции (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    import random
    import string
    
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.post(
        "/api/collections",
        headers=headers,
        json={
            "name": f"Test Collection {random_suffix}",
            "slug": f"test-collection-{random_suffix}",
            "season": "Spring",
            "year": 2024,
            "description": "Test collection description",
            "category": "unisex",
            "is_new": True,
            "is_featured": False
        }
    )
    # Может быть 201 (если админ) или 403 (если не админ)
    assert response.status_code in [201, 403]


@pytest.mark.asyncio
async def test_update_collection(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления коллекции (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.put(
        "/api/collections/999999",
        headers=headers,
        json={
            "name": "Updated Collection Name",
            "description": "Updated description"
        }
    )
    # Может быть 200 (если админ и коллекция существует) или 403/404
    assert response.status_code in [200, 403, 404]


@pytest.mark.asyncio
async def test_delete_collection(client: httpx.AsyncClient, auth_token: str):
    """Тест удаления коллекции (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.delete("/api/collections/999999", headers=headers)
    # Может быть 204 (если админ и коллекция существует) или 403/404
    assert response.status_code in [204, 403, 404]


@pytest.mark.asyncio
async def test_add_collection_image(client: httpx.AsyncClient, auth_token: str):
    """Тест добавления изображения в коллекцию (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Создаем тестовое изображение
    from io import BytesIO
    try:
        from PIL import Image
        
        # Создаем простое тестовое изображение
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        img_data = img_bytes.getvalue()
    except ImportError:
        # Если PIL не установлен, создаем простой PNG заголовок
        img_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d\x00\x00\x00d\x08\x02\x00\x00\x00\xff\x80\x02\x00'
    
    files = {"file": ("test.png", img_data, "image/png")}
    
    response = await client.post(
        "/api/collections/1/images",
        headers=headers,
        files=files
    )
    # Может быть 201 (если админ и коллекция существует) или 403/404
    assert response.status_code in [201, 403, 404]


@pytest.mark.asyncio
async def test_delete_collection_image(client: httpx.AsyncClient, auth_token: str):
    """Тест удаления изображения коллекции (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.delete("/api/collections/images/999999", headers=headers)
    # Может быть 204 (если админ и изображение существует) или 403/404
    assert response.status_code in [204, 403, 404]

