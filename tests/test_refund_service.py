from src.services.refund_service import RefundService
from psycopg.errors import UniqueViolation

class FakeOrderRepository:

    def get_order(self, order_id, customer_id):
        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": "Delivered",
        }

    def get_refund_eligibility(self, order_id, customer_id):
        return {
            "eligible": True,
        }

class FakeOrderRepositoryNotDelivered:

    def get_order(self, order_id, customer_id):
        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": "Shipped",
        }

    def get_refund_eligibility(self, order_id, customer_id):
        return {
            "eligible": False,
            "reason": "Order has not been delivered yet.",
        }


class FakeRefundRepository:

    def get_existing_refund(self, customer_id, order_id):
        return None

    def create_refund_request(
        self,
        customer_id,
        order_id,
        reason,
    ):
        return {
            "id": "test-refund-001",
            "status": "pending",
        }
    def get_refund_status(self, customer_id, order_id):
        return {
        "refund_request_id": "test-refund-001",
        "order_id": order_id,
        "status": "pending",
    }


def test_create_refund_request_success():

    service = RefundService(
        order_repository=FakeOrderRepository(),
        refund_repository=FakeRefundRepository(),
    )

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12348",
        reason="Product is defective",
    )

    assert result["status"] == "submitted"
    assert result["order_id"] == "12348"
    assert result["reason"] == "Product is defective"
    assert result["refund_status"] == "pending"
    assert result["refund_request_id"] == "test-refund-001"

class FakeRefundRepositoryWithExistingRefund:

    def get_existing_refund(self, customer_id, order_id):
        return {
            "id": "existing-refund-123",
            "status": "pending",
        }

    def create_refund_request(
        self,
        customer_id,
        order_id,
        reason,
    ):
        raise AssertionError(
            "create_refund_request should not be called"
        )

def test_create_refund_request_already_exists():

    service = RefundService(
        order_repository=FakeOrderRepository(),
        refund_repository=FakeRefundRepositoryWithExistingRefund(),
    )

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12348",
        reason="Product is defective",
    )

    assert result["status"] == "already_exists"
    assert result["refund_request_id"] == "existing-refund-123"
    assert result["order_id"] == "12348"
    assert result["refund_status"] == "pending"

class FakeOrderRepositoryWrongCustomer:

    def get_order(self, order_id, customer_id):
        return None

    def get_refund_eligibility(self, order_id, customer_id):
        raise AssertionError(
            "get_refund_eligibility should not be called"
        )

class FakeOrderRepositoryExpiredRefund:

    def get_order(self, order_id, customer_id):
        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "status": "Delivered",
        }

    def get_refund_eligibility(self, order_id, customer_id):
        return {
            "eligible": False,
            "reason": "The 7-day refund window has expired.",
        }

def test_create_refund_request_wrong_customer():

    service = RefundService(
        order_repository=FakeOrderRepositoryWrongCustomer(),
        refund_repository=FakeRefundRepository(),
    )

    result = service.create_refund_request(
        customer_id="customer-999",
        order_id="12348",
        reason="Product is defective",
    )

    assert result["status"] == "rejected"
    assert result["reason"] == (
        "Order not found for this customer."
    )

def test_get_refund_status_success():

    service = RefundService(
        order_repository=FakeOrderRepository(),
        refund_repository=FakeRefundRepository(),
    )

    result = service.get_refund_status(
        customer_id="customer-002",
        order_id="12348",
    )

    assert result["refund_request_id"] == "test-refund-001"
    assert result["order_id"] == "12348"
    assert result["status"] == "pending"

from psycopg.errors import UniqueViolation


class FakeRefundRepositoryRaceCondition:

    def get_existing_refund(self, customer_id, order_id):
        return {
            "id": "existing-refund-race",
            "status": "pending",
        }

    def create_refund_request(
        self,
        customer_id,
        order_id,
        reason,
    ):
        raise UniqueViolation(
            'duplicate key value violates unique constraint'
        )

def test_create_refund_request_handles_duplicate_from_database():
    service = RefundService(
        order_repository=FakeOrderRepository(),
        refund_repository=FakeRefundRepositoryRaceCondition(),
    )

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12348",
        reason="Product is defective",
    )

    assert result["status"] == "already_exists"

def test_create_refund_request_order_not_delivered():

    service = RefundService(
        order_repository=FakeOrderRepositoryNotDelivered(),
        refund_repository=FakeRefundRepository(),
    )

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12346",
        reason="Product is defective",
    )

    assert result["status"] == "rejected"
    assert result["reason"] == (
        "Order has not been delivered yet."
    )

def test_create_refund_request_expired_window():

    service = RefundService(
        order_repository=FakeOrderRepositoryExpiredRefund(),
        refund_repository=FakeRefundRepository(),
    )

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12345",
        reason="Product is defective",
    )

    assert result["status"] == "rejected"
    assert result["reason"] == (
        "The 7-day refund window has expired."
    )
