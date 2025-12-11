"""
Общие фикстуры для тестов
"""
import pytest
import httpx
from typing import Optional

BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "string"


@pytest.fixture
async def client():
    """HTTP клиент для запросов к API"""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac


@pytest.fixture
async def auth_token(client: httpx.AsyncClient) -> Optional[str]:
    """Получает токен аутентификации для тестового пользователя"""
    try:
        response = await client.post(
            "/api/auth/token",
            data={
                "username": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass
    return None


@pytest.fixture
async def auth_headers(auth_token: Optional[str]) -> dict:
    """Заголовки с токеном аутентификации"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

