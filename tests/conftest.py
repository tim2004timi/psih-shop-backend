"""
Общие фикстуры для тестов.
"""
import os

os.environ.setdefault("POSTGRES_DB", "test_db")
os.environ.setdefault("POSTGRES_USER", "test_user")
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("MINIO_ROOT_USER", "minioadmin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "minioadmin")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("BACKEND_PUBLIC_BASE_URL", "http://testserver")
os.environ.setdefault("FRONTEND_PUBLIC_BASE_URL", "http://frontend.test")

from typing import Optional

import httpx
import pytest
from httpx import ASGITransport

from src.main import app
from src.database import AsyncSessionLocal, engine
from src.models.base import Base
from src.models.category import Category, ProductCategory
from src.models.collection import Collection, CollectionCategory, CollectionProduct
from src.models.product import Product, ProductColor, ProductSize
from src.models.user import User
from src.utils import get_password_hash

TEST_USER_EMAIL = "user@example.com"
TEST_USER_PASSWORD = "string"


@pytest.fixture(autouse=True)
async def reset_database(monkeypatch):
    from src.routers import cdek as cdek_router
    from src.routers import collection as collection_router
    from src.routers import orders as orders_router
    from src.routers import product as product_router
    from src.routers import site_settings as settings_router

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        admin = User(
            email=TEST_USER_EMAIL,
            password_hash=get_password_hash(TEST_USER_PASSWORD),
            first_name="Admin",
            last_name="User",
            is_admin=True,
            email_verified=True,
            is_active=True,
        )
        regular_user = User(
            email="customer@example.com",
            password_hash=get_password_hash("customer-password"),
            first_name="Regular",
            last_name="Customer",
            is_admin=False,
            email_verified=True,
            is_active=True,
        )

        session.add_all([admin, regular_user])
        await session.flush()

        product = Product(
            description="Seed product description",
            price="100.00",
            weight=0.5,
            currency="RUB",
        )
        session.add(product)
        await session.flush()

        product_color = ProductColor(
            product_id=product.id,
            slug="seed-product",
            title="Seed Product",
            label="Black",
            hex="#000000",
        )
        session.add(product_color)
        await session.flush()

        product_size = ProductSize(
            product_color_id=product_color.id,
            size="M",
            quantity=10,
            sort_order=0,
        )
        session.add(product_size)

        category = Category(
            name="Outerwear",
            slug="outerwear",
            level=0,
            sort_order=0,
            is_active=True,
        )
        session.add(category)
        await session.flush()

        session.add(ProductCategory(product_id=product.id, category_id=category.id, sort_order=0))

        collection = Collection(
            name="Seed Collection",
            slug="seed-collection",
            season="Spring",
            year=2024,
            description="Seed collection",
            category=CollectionCategory.UNISEX,
            is_new=True,
            is_featured=False,
        )
        session.add(collection)
        await session.flush()
        session.add(CollectionProduct(collection_id=collection.id, product_id=product.id, sort_order=0))

        await session.commit()

    async def fake_upload_image(file):
        return f"http://testserver/media/{file.filename}"

    class FakeCDEKClient:
        async def get_suggest_cities(self, city_name: str):
            return [{
                "city_uuid": "city-1",
                "code": 123,
                "full_name": f"{city_name} test city",
                "country_code": "RU",
            }]

        async def get_offices_by_city_code(self, city_code: int, office_type: str = "PVZ"):
            return [{
                "code": "PVZ-1",
                "uuid": "office-1",
                "type": office_type,
                "work_time": "09:00-18:00",
                "location": {
                    "city_code": city_code,
                    "city": "Taganrog",
                    "longitude": 38.9,
                    "latitude": 47.2,
                    "address": "Test address",
                },
            }]

        async def add_order_to_cdek(self, order_id: int, shipment_point: str, delivery_point: str, db):
            return "cdek-order-uuid"

    monkeypatch.setattr(product_router, "upload_image", fake_upload_image)
    monkeypatch.setattr(collection_router, "upload_image", fake_upload_image)
    monkeypatch.setattr(settings_router, "upload_image", fake_upload_image)
    monkeypatch.setattr(cdek_router, "get_cdek_client", lambda: FakeCDEKClient())
    monkeypatch.setattr(orders_router, "get_cdek_client", lambda: FakeCDEKClient())


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=30.0) as ac:
        yield ac


@pytest.fixture
async def auth_token(client: httpx.AsyncClient) -> Optional[str]:
    response = await client.post(
        "/api/auth/token",
        data={
            "username": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def auth_headers(auth_token: Optional[str]) -> dict:
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}


@pytest.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session

