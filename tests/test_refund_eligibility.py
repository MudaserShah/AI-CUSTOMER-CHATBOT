from src.database.order_repository import OrderRepository


def test_delivered_order_is_refund_eligible():
    repo = OrderRepository()

    result = repo.get_refund_eligibility(
        "12348",
        "customer-002",
    )

    assert result["eligible"] is True
    assert result["order_id"] == "12348"
    assert result["customer_id"] == "customer-002"
    assert result["status"] == "Delivered"
    assert result["refund_deadline"] is not None


def test_wrong_customer_cannot_get_refund_eligibility():
    repo = OrderRepository()

    result = repo.get_refund_eligibility(
        "12348",
        "customer-003",
    )

    assert result["eligible"] is False


def test_nonexistent_order_is_not_refund_eligible():
    repo = OrderRepository()

    result = repo.get_refund_eligibility(
        "99999",
        "customer-002",
    )

    assert result["eligible"] is False


def test_shipped_order_is_not_refund_eligible():
    repo = OrderRepository()

    result = repo.get_refund_eligibility(
        "12346",
        "customer-002",
    )

    assert result["eligible"] is False
    assert result["reason"] == "Order has not been delivered yet."