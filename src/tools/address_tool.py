from langchain_core.tools import tool
from pydantic import BaseModel, Field, EmailStr


class AddressInput(BaseModel):

    order_id: str = Field(
        ...,
        pattern=r"^[0-9]{5}$",
        description="The 5-digit order ID"
    )

    new_address: str = Field(
        ...,
        min_length=5,
        description="The new delivery address"
    )
    provided_email: EmailStr = Field(
    ...,
    description="The email address associated with the customer account"
)


@tool(args_schema=AddressInput)
def change_delivery_address(
    order_id: str,
    new_address: str,
    provided_email: str,
):
    """
    Request a delivery address change for an order.

    Customer identity is handled by the agent layer.
    """

    return {
        "order_id": order_id,
        "new_address": new_address,
        "provided_email": provided_email,
        "status": "ready_for_update",
    }


if __name__ == "__main__":

    result = change_delivery_address.invoke({
        "order_id": "12346",
        "new_address": "House 500, Street 20, Wah Cantt",
        "provided_email": "ali@example.com",
    })

    print("Result:")
    print(result)

    print("\nTool Name:")
    print(change_delivery_address.name)

    print("\nTool Description:")
    print(change_delivery_address.description)

    print("\nTool Args:")
    print(
        change_delivery_address.args_schema.model_json_schema()
    )