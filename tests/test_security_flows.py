import pytest

from src.models.orders import Order
from src.routers import cdek as cdek_router
from src.routers import payments as payments_router


async def _create_guest_order(client):
    response = await client.post(
        "/api/orders",
        json={
            "order": {
                "email": "guest@example.com",
                "first_name": "Guest",
                "last_name": "User",
            },
            "products": [
                {
                    "product_size_id": 1,
                    "quantity": 1,
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_guest_order_returns_access_token(client):
    order = await _create_guest_order(client)
    assert order["access_token"]


@pytest.mark.asyncio
async def test_guest_payment_init_requires_access_token(client, monkeypatch):
    order = await _create_guest_order(client)

    async def fake_init_payment(**kwargs):
        return {
            "Success": True,
            "PaymentURL": "https://pay.test/redirect",
            "PaymentId": 12345,
        }

    monkeypatch.setattr(payments_router.tbank_client, "init_payment", fake_init_payment)

    forbidden_response = await client.post(
        "/api/payments/init",
        json={"order_id": order["id"]},
    )
    assert forbidden_response.status_code == 403

    allowed_response = await client.post(
        "/api/payments/init",
        json={"order_id": order["id"], "access_token": order["access_token"]},
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["success"] is True


@pytest.mark.asyncio
async def test_guest_cdek_order_info_requires_access_token(client, db_session, monkeypatch):
    order = await _create_guest_order(client)

    db_order = await db_session.get(Order, order["id"])
    db_order.cdek_uuid = "cdek-uuid-1"
    await db_session.commit()

    class FakeCDEKClient:
        async def get_order_info_by_uuid(self, uuid: str):
            return {"uuid": uuid, "cdek_number": "CDEK-100"}

    monkeypatch.setattr(cdek_router, "get_cdek_client", lambda: FakeCDEKClient())

    forbidden_response = await client.get("/api/cdek/order/cdek-uuid-1")
    assert forbidden_response.status_code == 403

    allowed_response = await client.get(
        "/api/cdek/order/cdek-uuid-1",
        params={"access_token": order["access_token"]},
    )
    assert allowed_response.status_code == 200
    assert allowed_response.json()["uuid"] == "cdek-uuid-1"
