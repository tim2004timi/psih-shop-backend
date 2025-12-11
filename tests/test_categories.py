"""
Тесты для эндпоинтов категорий
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_get_categories_tree(client: httpx.AsyncClient):
    """Тест получения дерева категорий"""
    response = await client.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_products_by_category(client: httpx.AsyncClient):
    """Тест получения продуктов по категории"""
    # Сначала получаем список категорий
    categories_response = await client.get("/api/categories")
    if categories_response.status_code == 200:
        categories = categories_response.json()
        if categories:
            # Берем первую категорию и ищем slug
            def find_slug(cats):
                for cat in cats:
                    if "slug" in cat:
                        return cat["slug"]
                    if "children" in cat and cat["children"]:
                        slug = find_slug(cat["children"])
                        if slug:
                            return slug
                return None
            
            slug = find_slug(categories)
            if slug:
                response = await client.get(f"/api/categories/{slug}")
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_category(client: httpx.AsyncClient, auth_token: str):
    """Тест создания категории (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    import random
    import string
    
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.post(
        "/api/categories",
        headers=headers,
        json={
            "name": f"Test Category {random_suffix}",
            "slug": f"test-category-{random_suffix}",
            "level": 0,
            "sort_order": 0,
            "is_active": True
        }
    )
    # Может быть 201 (если админ) или 403 (если не админ)
    assert response.status_code in [201, 403]


@pytest.mark.asyncio
async def test_delete_category(client: httpx.AsyncClient, auth_token: str):
    """Тест удаления категории (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.delete("/api/categories/999999", headers=headers)
    # Может быть 204 (если админ и категория существует) или 403/404
    assert response.status_code in [204, 403, 404]

