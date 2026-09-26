from src.database.order_repository import OrderRepository
from src.database.refund_repository import RefundRepository
from psycopg.errors import UniqueViolation


class RefundService:

    def __init__(
        self,
        order_repository=None,
        refund_repository=None,
    ):
        self.order_repository = (
            order_repository or OrderRepository()
        )

        self.refund_repository = (
            refund_repository or RefundRepository()
        )

    def create_refund_request(
        self,
        customer_id: str,
        order_id: str,
        reason: str,
    ):

        # 1. Check whether the order belongs to the customer
        order = self.order_repository.get_order(
            order_id,
            customer_id,
        )

        if order is None:
            return {
                "status": "rejected",
                "order_id": order_id,
                "reason": "Order not found for this customer.",
            }

        # 2. Check refund eligibility
        eligibility = self.order_repository.get_refund_eligibility(
            order_id,
            customer_id,
        )

        if not eligibility["eligible"]:
            return {
                "status": "rejected",
                "order_id": order_id,
                "reason": eligibility["reason"],
            }

        # 3. Check whether a refund already exists
        existing_refund = (
            self.refund_repository.get_existing_refund(
                customer_id,
                order_id,
            )
        )

        if existing_refund is not None:
            return {
                "status": "already_exists",
                "refund_request_id": existing_refund["id"],
                "order_id": order_id,
                "refund_status": existing_refund["status"],
                "message": (
                    "A refund request already exists "
                    "for this order."
                ),
            }

        # 4. Create refund request
        try:
            refund_request = (
               self.refund_repository.create_refund_request(
            customer_id=customer_id,
            order_id=order_id,
            reason=reason,
        )
    )

        except UniqueViolation:
            existing_refund = (
              self.refund_repository.get_existing_refund(
            customer_id,
            order_id,
        )
    )

            if existing_refund is not None:
                return {
            "status": "already_exists",
            "refund_request_id": existing_refund["id"],
            "order_id": order_id,
            "refund_status": existing_refund["status"],
            "message": (
                "A refund request already exists "
                "for this order."
            ),
        }

            raise

        return {
            "status": "submitted",
            "refund_request_id": refund_request["id"],
            "order_id": order_id,
            "reason": reason,
            "refund_status": refund_request["status"],
        }

    def get_refund_status(
    self,
    customer_id: str,
    order_id: str,
):
         return self.refund_repository.get_refund_status(
        customer_id,
        order_id,
    )

if __name__ == "__main__":

    service = RefundService()

    result = service.create_refund_request(
        customer_id="customer-002",
        order_id="12345",
        reason="Product is defective",
    )

    print(result)