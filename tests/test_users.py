"""
Тесты для эндпоинтов пользователей
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_update_current_user_info(client: httpx.AsyncClient, auth_token: str):
    """Тест обновления информации о текущем пользователе"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.put(
        "/api/users/me",
        headers=headers,
        json={
            "first_name": "Updated",
            "last_name": "Name"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"


@pytest.mark.asyncio
async def test_get_user_by_id(client: httpx.AsyncClient, auth_token: str):
    """Тест получения пользователя по ID"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Сначала получаем свой ID
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["id"]
    
    # Получаем пользователя по ID
    response = await client.get(f"/api/users/{user_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_get_users_list(client: httpx.AsyncClient, auth_token: str):
    """Тест получения списка пользователей (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/users?skip=0&limit=10", headers=headers)
    # Может быть 200 (если админ) или 403 (если не админ)
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_activate_user(client: httpx.AsyncClient, auth_token: str):
    """Тест активации пользователя (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Получаем свой ID
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["id"]
    
    response = await client.put(f"/api/users/{user_id}/activate", headers=headers)
    # Может быть 200 (если админ) или 403 (если не админ)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_deactivate_user(client: httpx.AsyncClient, auth_token: str):
    """Тест деактивации пользователя (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Получаем свой ID
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["id"]
    
    response = await client.put(f"/api/users/{user_id}/deactivate", headers=headers)
    # Может быть 200 (если админ) или 403 (если не админ)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_verify_email(client: httpx.AsyncClient, auth_token: str):
    """Тест подтверждения email"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    # Получаем свой ID
    me_response = await client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200
    user_id = me_response.json()["id"]
    
    response = await client.put(f"/api/users/{user_id}/verify-email", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email_verified"] is True


@pytest.mark.asyncio
async def test_search_user_by_email(client: httpx.AsyncClient, auth_token: str):
    """Тест поиска пользователя по email (только для админов)"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/users/search/user@example.com", headers=headers)
    # Может быть 200 (если админ) или 403 (если не админ)
    assert response.status_code in [200, 403]
    if response.status_code == 200:
        data = response.json()
        # Может быть None если не найден, или dict если найден
        assert data is None or isinstance(data, dict)

