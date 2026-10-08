from src.database.order_repository import OrderRepository
from src.database.refund_repository import RefundRepository


class OrderService:
    def __init__(self, order_repository=None, refund_repository=None):
        self.order_repository = order_repository or OrderRepository()
        self.refund_repository = refund_repository or RefundRepository()

    def _decorate(self, order: dict) -> dict:
        eligibility = self.order_repository.get_refund_eligibility(
            order["order_id"],
            order["customer_id"],
        )
        refund = self.refund_repository.get_refund_status(
            order["customer_id"],
            order["order_id"],
        )

        return {
            **order,
            "refund_eligible": eligibility["eligible"],
            "refund_reason": None if eligibility["eligible"] else eligibility.get("reason"),
            "refund_deadline": eligibility.get("refund_deadline"),
            "refund_status": refund["status"] if refund else None,
            "refund_request_id": refund["id"] if refund else None,
        }

    def list_orders(self, customer_id: str) -> list[dict]:
        return [
            self._decorate(order)
            for order in self.order_repository.get_customer_orders(customer_id)
        ]

    def get_order(self, customer_id: str, order_id: str) -> dict | None:
        order = self.order_repository.get_order(order_id, customer_id)
        return self._decorate(order) if order else None
