from langchain_core.tools import tool
from pydantic import BaseModel, Field
# from src.database.order_repository import OrderRepository

class OrderInput(BaseModel):
    order_id: str =Field(..., pattern=r"^[0-9]{5}$", description="The 5-digit unique order identifier")

# order_repository = OrderRepository()


@tool(args_schema=OrderInput)
def get_order(order_id: str):
    """
    Retrieve the customer's order using the 5-digit order ID.
    """
    
    return {
        "order_id": order_id
    }
#     """This tool retrieves the current status and delivery-related information of a specific order using its order ID."""
    
#     order = order_repository.get_order(order_id)
#     if order is None:
#         return {
#     "order_id": order_id,
#     "status": "not_found",
#     "message": "Invalid order ID"
# }
#     return order

if __name__ == "__main__":
     

    search_id = "12345"

    result = get_order.invoke({
           "order_id": search_id
        })
    
        
    print(f"Order ID {search_id} ka status hai :")
    print(result)
    print("Tool Name:", get_order.name)
    print("Tool Description:", get_order.description)
    print("Tool Args:", get_order.args_schema.model_json_schema())
    