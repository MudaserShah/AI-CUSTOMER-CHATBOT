from src.database.order_repository import OrderRepository
from src.services.verification_service import VerificationService


class AddressService:

    def __init__(
    self,
    order_repository=None,
    verification_service=None,
):
        self.order_repository = (
        order_repository or OrderRepository()
    )

        self.verification_service = (
        verification_service or VerificationService()
    )

    def change_delivery_address(
        self,
        customer_id: str,
        order_id: str,
        new_address: str,
        provided_email: str,
    ):
        verification = self.verification_service.verify_customer(
        customer_id=customer_id,
        provided_email=provided_email,
)

        if not verification["verified"]:
            return {
        "status": "rejected",
        "reason": verification["reason"],
    }
        order = self.order_repository.get_order(
            order_id,
            customer_id,
        )

        if order is None:
            return {
                "status": "rejected",
                "reason": "Order not found for this customer.",
            }

        if order["status"] == "Delivered":
            return {
                "status": "rejected",
                "reason": "Delivery address cannot be changed after the order is delivered.",
            }

        updated_order = self.order_repository.update_delivery_address(
            order_id=order_id,
            customer_id=customer_id,
            new_address=new_address,
        )

        if updated_order is None:
            return {
                "status": "failed",
                "reason": "Unable to update delivery address.",
            }

        return {
            "status": "updated",
            "order_id": updated_order["order_id"],
            "delivery_address": updated_order["delivery_address"],
        }


if __name__ == "__main__":

    service = AddressService()

    result = service.change_delivery_address(
        customer_id="customer-003",
        order_id="12346",
        new_address="House 500, Street 20, Wah Cantt",
        provided_email="ahmed@example.com",
    )

    print(result)