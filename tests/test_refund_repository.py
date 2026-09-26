import pytest
from psycopg.errors import UniqueViolation
from src.database.refund_repository import RefundRepository


def test_get_refund_status_existing_refund():

    repo = RefundRepository()

    result = repo.get_refund_status(
        customer_id="customer-002",
        order_id="12348",
    )

    assert result is not None
    assert result["customer_id"] == "customer-002"
    assert result["order_id"] == "12348"
    assert result["status"] == "pending"
    assert result["reason"] == "product is defective"

def test_get_refund_status_wrong_customer():

    repo = RefundRepository()

    result = repo.get_refund_status(
        customer_id="customer-003",
        order_id="12348",
    )

    assert result is None

def test_get_refund_status_nonexistent_refund():

    repo = RefundRepository()

    result = repo.get_refund_status(
        customer_id="customer-002",
        order_id="99999",
    )

    assert result is None

def test_get_existing_refund():

    repo = RefundRepository()

    result = repo.get_existing_refund(
        customer_id="customer-002",
        order_id="12348",
    )

    assert result is not None
    assert result["customer_id"] == "customer-002"
    assert result["order_id"] == "12348"
    assert result["status"] == "pending"
    assert result["reason"] == "product is defective"

def test_get_existing_refund_wrong_customer():

    repo = RefundRepository()

    result = repo.get_existing_refund(
        customer_id="customer-003",
        order_id="12348",
    )

    assert result is None

def test_get_existing_refund_nonexistent():

    repo = RefundRepository()

    result = repo.get_existing_refund(
        customer_id="customer-002",
        order_id="99999",
    )

    assert result is None

def test_create_refund_request():

    repo = RefundRepository()

    result = repo.create_refund_request(
        customer_id="customer-002",
        order_id="88888",
        reason="Product is defective",
    )

    assert result is not None
    assert result["customer_id"] == "customer-002"
    assert result["order_id"] == "88888"
    assert result["reason"] == "Product is defective"
    assert result["status"] == "pending"
    assert result["id"] is not None
    assert result["created_at"] is not None

def test_create_refund_request_duplicate():

    repo = RefundRepository()

    with pytest.raises(UniqueViolation):
        repo.create_refund_request(
            customer_id="customer-002",
            order_id="12348",
            reason="Duplicate test refund",
        )

    result = repo.get_existing_refund(
        customer_id="customer-002",
        order_id="12348",
    )

    assert result is not None
    assert result["customer_id"] == "customer-002"
    assert result["order_id"] == "12348"
    assert result["status"] == "pending"
    assert result["reason"] == "product is defective"
    repo = RefundRepository()

    with pytest.raises(UniqueViolation):
        repo.create_refund_request(
            customer_id="customer-002",
            order_id="12348",
            reason="Duplicate test refund",
        )