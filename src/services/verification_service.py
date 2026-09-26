from src.database.repository import CustomerRepository


class VerificationService:

    def __init__(self, customer_repository=None):
        self.customer_repository = (
            customer_repository or CustomerRepository()
        )

    def verify_customer(
        self,
        customer_id: str,
        provided_email: str,
    ):
        actual_email = self.customer_repository.get_customer_email(
            customer_id
        )

        if actual_email is None:
            return {
                "verified": False,
                "reason": "Customer not found.",
            }

        if actual_email.lower() != provided_email.lower():
            return {
                "verified": False,
                "reason": "Email verification failed.",
            }

        return {
            "verified": True,
            "message": "Customer identity verified.",
        }


if __name__ == "__main__":

    service = VerificationService()

    print(
        service.verify_customer(
            "customer-002",
            "ali@example.com",
        )
    )

    print(
        service.verify_customer(
            "customer-002",
            "wrong@example.com",
        )
    )

    print(
        service.verify_customer(
            "customer-999",
            "anything@example.com",
        )
    )