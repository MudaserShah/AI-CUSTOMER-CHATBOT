from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.auth.jwt_utils import create_access_token
from src.rate_limit import limiter
from src.routes.refund_routes import router

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.include_router(router)

client = TestClient(app)


def auth_headers(customer_id: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token(customer_id)}"}


def test_create_refund_route_success():

    response = client.post(
        "/refund",
        headers=auth_headers("customer-002"),
        json={
            "order_id": "12345",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in [
        "submitted",
        "already_exists",
    ]

def test_create_refund_route_invalid_order_id():

    response = client.post(
        "/refund",
        headers=auth_headers("customer-002"),
        json={
            "order_id": "123",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 422

def test_create_refund_route_missing_reason():

    response = client.post(
        "/refund",
        headers=auth_headers("customer-002"),
        json={
            "order_id": "12345",
        },
    )

    assert response.status_code == 422


def test_create_refund_route_wrong_customer():
    # Authenticated AS customer-999 (via the token), attempting to
    # refund an order that belongs to customer-002. There is no
    # customer_id field in the body anymore to "get wrong" — this
    # test exists specifically to prove the authenticated identity
    # itself is what gets checked (F2's whole point).
    response = client.post(
        "/refund",
        headers=auth_headers("customer-999"),
        json={
            "order_id": "12345",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["reason"] == "Order not found for this customer."


def test_create_refund_route_missing_auth():
    response = client.post(
        "/refund",
        json={
            "order_id": "12345",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 401


def test_get_refund_status_route_success():

    response = client.get(
        "/refund/12348",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "found"
    assert data["order_id"] == "12348"
    assert data["refund_status"] == "pending"
    assert data["refund_request_id"] is not None
    assert data["reason"] == "product is defective"


def test_get_refund_status_route_wrong_customer():
    # Same idea as above, for the GET path: authenticated as the
    # wrong customer should behave exactly like the refund doesn't
    # exist for them, never leak another customer's refund status.
    response = client.get(
        "/refund/12348",
        headers=auth_headers("customer-999"),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"
    assert data["order_id"] == "12348"


def test_get_refund_status_route_nonexistent():

    response = client.get(
        "/refund/99999",
        headers=auth_headers("customer-002"),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"
    assert data["order_id"] == "99999"


def test_get_refund_status_route_missing_auth():
    response = client.get("/refund/12348")
    assert response.status_code == 401
