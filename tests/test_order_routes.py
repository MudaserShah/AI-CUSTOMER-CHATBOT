from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.auth.jwt_utils import create_access_token
from src.rate_limit import limiter
from src.routes.order_routes import router


app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(router)

client = TestClient(app)


def auth_headers(customer_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(customer_id)}"}


def test_get_order_success():
    response = client.get(
        "/orders/12346",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_id"] == "12346"
    assert data["status"] is not None
    assert "items" in data
    assert "total_amount" in data


def test_get_order_wrong_customer():
    response = client.get(
        "/orders/12346",
        headers=auth_headers("customer-003"),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."


def test_get_order_nonexistent():
    response = client.get(
        "/orders/99999",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."


def test_get_order_invalid_order_id():
    response = client.get(
        "/orders/123",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 422


def test_get_order_missing_auth():
    response = client.get("/orders/12346")

    assert response.status_code == 401


def test_get_order_invalid_token():
    response = client.get(
        "/orders/12346",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_list_orders_success():
    response = client.get(
        "/orders",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for order in data:
        assert "order_id" in order
        assert "status" in order
        assert "items" in order


def test_list_orders_missing_auth():
    response = client.get("/orders")

    assert response.status_code == 401
