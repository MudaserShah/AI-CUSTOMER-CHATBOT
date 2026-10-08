from decimal import Decimal

import pytest

from src.schemas.store_schemas import CheckoutItem, CheckoutRequest
from src.services.store_service import ExistingCustomerCheckoutError, StoreService


class FakeCustomerRepository:
    def __init__(self, existing=None):
        self.existing = existing
        self.created = None

    def get_customer_by_email(self, email):
        return self.existing

    def get_customer(self, customer_id):
        if self.existing and self.existing[1] == customer_id:
            return self.existing
        return None

    def create_customer(self, customer_id, name, email):
        self.created = (customer_id, name, email)
        return (1, customer_id, name, email, "2026-10-05T00:00:00Z")


class FakeOrderRepository:
    def __init__(self):
        self.created = None

    def create_order(self, **kwargs):
        self.created = kwargs
        return {
            "order_id": kwargs["order_id"],
            "customer_id": kwargs["customer_id"],
            "status": "Processing",
            "delivery_address": kwargs["delivery_address"],
            "total_amount": kwargs["total_amount"],
            "currency": kwargs["currency"],
            "payment_method": kwargs["payment_method"],
        }


def checkout_payload():
    return CheckoutRequest(
        name="Ali Khan",
        email="Ali@example.com",
        delivery_address="House 10, Street 2, Wah Cantt",
        items=[
            {"product_id": "usb-c-hub", "quantity": 2},
            {"product_id": "desk-speakers", "quantity": 1},
        ],
    )


def test_checkout_generates_server_side_customer_and_order_ids():
    customers = FakeCustomerRepository()
    orders = FakeOrderRepository()
    service = StoreService(customers, orders)

    result = service.checkout(checkout_payload())

    assert result["customer_id"].startswith("customer-")
    assert len(result["order_id"]) == 5
    assert result["order_id"].isdigit()
    assert customers.created[2] == "ali@example.com"
    assert result["total_amount"] == Decimal("207.00")
    assert orders.created["items"][0]["unit_price"] == "59.00"
    assert orders.created["items"][1]["unit_price"] == "89.00"


def test_checkout_does_not_accept_an_existing_email_without_authentication():
    existing = (1, "customer-existing", "Alice", "alice@example.com", "2026-10-01T00:00:00Z")
    customers = FakeCustomerRepository(existing=existing)
    orders = FakeOrderRepository()
    service = StoreService(customers, orders)

    payload = CheckoutRequest(
        name="Attacker",
        email="ALICE@EXAMPLE.COM",
        delivery_address="House 1, Street 1",
        items=[{"product_id": "usb-c-hub", "quantity": 1}],
    )

    with pytest.raises(ExistingCustomerCheckoutError):
        service.checkout(payload)

    assert orders.created is None


def test_checkout_uses_authenticated_customer_for_returning_customer():
    existing = (1, "customer-existing", "Alice", "alice@example.com", "2026-10-01T00:00:00Z")
    customers = FakeCustomerRepository(existing=existing)
    orders = FakeOrderRepository()
    service = StoreService(customers, orders)

    result = service.checkout(
        checkout_payload().model_copy(update={"email": "alice@example.com", "name": "Alice"}),
        authenticated_customer_id="customer-existing",
    )

    assert result["customer_id"] == "customer-existing"
    assert orders.created["customer_id"] == "customer-existing"


def test_checkout_rejects_unknown_product():
    service = StoreService(FakeCustomerRepository(), FakeOrderRepository())
    payload = checkout_payload().model_copy(
        update={
    "items": [
        CheckoutItem(product_id="does-not-exist", quantity=1)
    ]
}
    )

    with pytest.raises(ValueError, match="was not found"):
        service.checkout(payload)
