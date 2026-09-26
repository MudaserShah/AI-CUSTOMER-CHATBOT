from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.routes.refund_routes import router


app = FastAPI()
app.include_router(router)

client = TestClient(app)


def test_create_refund_route_success():

    response = client.post(
        "/refund",
        json={
            "customer_id": "customer-002",
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
        json={
            "customer_id": "customer-002",
            "order_id": "123",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 422

def test_create_refund_route_missing_reason():

    response = client.post(
        "/refund",
        json={
            "customer_id": "customer-002",
            "order_id": "12345",
        },
    )

    assert response.status_code == 422


def test_create_refund_route_wrong_customer():

    response = client.post(
        "/refund",
        json={
            "customer_id": "customer-999",
            "order_id": "12345",
            "reason": "Product is defective",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "rejected"
    assert data["reason"] == "Order not found for this customer."


def test_get_refund_status_route_success():

    response = client.get(
        "/refund/12348",
        params={
            "customer_id": "customer-002",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "found"
    assert data["order_id"] == "12348"
    assert data["refund_status"] == "pending"
    assert data["refund_request_id"] is not None
    assert data["reason"] == "product is defective"


def test_get_refund_status_route_wrong_customer():

    response = client.get(
        "/refund/12348",
        params={
            "customer_id": "customer-999",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"
    assert data["order_id"] == "12348"


def test_get_refund_status_route_nonexistent():

    response = client.get(
        "/refund/99999",
        params={
            "customer_id": "customer-002",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "not_found"
    assert data["order_id"] == "99999"