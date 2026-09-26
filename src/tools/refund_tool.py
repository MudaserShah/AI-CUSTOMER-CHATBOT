from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.services.refund_service import RefundService

# from src.database.refund_repository import RefundRepository
# from src.database.order_repository import OrderRepository


class RefundInput(BaseModel):
    order_id: str = Field(
        ...,
        pattern=r"^[0-9]{5}$",
        description="The 5-digit order ID for which the customer wants a refund"
    )

    reason: str = Field(
        ...,
        min_length=3,
        description="The reason why the customer wants a refund"
    )

# order_repository = OrderRepository()
# refund_repository = RefundRepository()
refund_service = RefundService()


@tool(args_schema=RefundInput)
def create_refund_request(
    order_id: str,
    reason: str,
):
    """
    Create a refund request for a customer's order.

    Customer identity is handled by the agent layer.
    """

    return {
        "order_id": order_id,
        "reason": reason,
        "status": "ready_for_submission"
    }


if __name__ == "__main__":

    result = create_refund_request.invoke({
        "order_id": "12345",
        "reason": "Product is defective"
    })

    print("Result:")
    print(result)

    print("\nTool Name:")
    print(create_refund_request.name)

    print("\nTool Description:")
    print(create_refund_request.description)

    print("\nTool Args:")
    print(
        create_refund_request.args_schema.model_json_schema()
    )