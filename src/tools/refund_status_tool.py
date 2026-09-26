from langchain_core.tools import tool
from pydantic import BaseModel, Field

# from src.database.refund_repository import RefundRepository


class RefundStatusInput(BaseModel):

    order_id: str = Field(
        ...,
        pattern=r"^[0-9]{5}$",
        description="The 5-digit order ID"
    )


# refund_repository = RefundRepository()


@tool(args_schema=RefundStatusInput)
def get_refund_status(order_id: str):
    """
    Get the current refund request status for an order.

    Customer identity is handled by the agent layer.
    """

    return {
        "order_id": order_id,
        "status": "requires_customer_context"
    }


if __name__ == "__main__":

    from langchain_core.tools import tool
from pydantic import BaseModel, Field

# from src.database.refund_repository import RefundRepository


class RefundStatusInput(BaseModel):

    order_id: str = Field(
        ...,
        pattern=r"^[0-9]{5}$",
        description="The 5-digit order ID"
    )


# refund_repository = RefundRepository()


@tool(args_schema=RefundStatusInput)
def get_refund_status(order_id: str):
    """
    Get the current refund request status for an order.

    Customer identity is handled by the agent layer.
    """

    return {
        "order_id": order_id,
        "status": "requires_customer_context"
    }


if __name__ == "__main__":

    result = get_refund_status.invoke({"order_id": "12345"})
    print(result)