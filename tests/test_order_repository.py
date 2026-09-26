from src.database.order_repository import OrderRepository


def test_get_existing_order():
    repo = OrderRepository()

    order = repo.get_order("12346", "customer-002")

    assert order is not None
    assert order["order_id"] == "12346"
    assert order["customer_id"] == "customer-002"


def test_get_order_wrong_customer():
    repo = OrderRepository()

    order = repo.get_order("12346", "customer-003")

    assert order is None


def test_get_nonexistent_order():
    repo = OrderRepository()

    order = repo.get_order("99999", "customer-002")

    assert order is None