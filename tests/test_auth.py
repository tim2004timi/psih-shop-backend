"""
Тесты для эндпоинтов аутентификации
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_login_success(client: httpx.AsyncClient):
    """Тест успешного входа"""
    response = await client.post(
        "/api/auth/token",
        data={
            "username": "user@example.com",
            "password": "string"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "user@example.com"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: httpx.AsyncClient):
    """Тест входа с неверными учетными данными"""
    response = await client.post(
        "/api/auth/token",
        data={
            "username": "user@example.com",
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_user_not_found(client: httpx.AsyncClient):
    """Тест входа несуществующего пользователя"""
    response = await client.post(
        "/api/auth/token",
        data={
            "username": "nonexistent@example.com",
            "password": "password"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client: httpx.AsyncClient):
    """Тест регистрации нового пользователя"""
    import random
    import string
    
    # Генерируем уникальный email
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"test_{random_suffix}@example.com"
    
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email


@pytest.mark.asyncio
async def test_register_duplicate_email(client: httpx.AsyncClient):
    """Тест регистрации с существующим email"""
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "first_name": "Test",
            "last_name": "User"
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user(client: httpx.AsyncClient, auth_token: str):
    """Тест получения информации о текущем пользователе"""
    if not auth_token:
        pytest.skip("Auth token not available")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert "id" in data
    assert "first_name" in data
    assert "last_name" in data


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: httpx.AsyncClient):
    """Тест получения информации о пользователе без токена"""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: httpx.AsyncClient):
    """Тест получения информации о пользователе с невалидным токеном"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = await client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401

