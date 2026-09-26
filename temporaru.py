import json
from pathlib import Path
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from src.database.order_repository import OrderRepository

# def load_order_data(json_file_name):
    
#     current_dir = Path(__file__).parent.resolve()
#     file_path= current_dir / json_file_name
#     with open(file_path, 'r') as file:
#         return json.load(file)

# all_orders = load_order_data("orders.json")
class OrderInput(BaseModel):
    order_id: str =Field(..., pattern=r"^[0-9]{5}$", description="The 5-digit unique order identifier")

# class OrderRepository:
#     def __init__(self, file_name: str = "orders.json"):
#         self.file_path = Path(__file__).parent.resolve() / file_name
#         self.orders = self._load_orders()

#     def _load_orders(self):
#         with open(self.file_path, "r") as file:
#             orders_list = json.load(file)
#             return {
#                 order["order_id"]: order
#                 for order in orders_list
#             }

#     def get_order(self, order_id: str):
#         return self.orders.get(order_id, None)


order_repository = OrderRepository()



@tool(args_schema=OrderInput)
def get_order(order_id: str):
    """This tool retrieves the current status and delivery-related information of a specific order using its order ID."""
    
    # for order in all_orders:
    #     if order["order_id"] == order_id:
    #         return order
    
    order = order_repository.get_order(order_id)
    if order is None:
        return {
    "order_id": order_id,
    "status": "not_found",
    "message": "Invalid order ID"
}
    return order

if __name__ == "__main__":
     

    search_id = "12345"
        # status = get_order(search_id, all_orders)
    result = get_order.invoke({
           "order_id": search_id
        })
    
        
    print(f"Order ID {search_id} ka status hai :")
    print(result)
    print("Tool Name:", get_order.name)
    print("Tool Description:", get_order.description)
    print("Tool Args:", get_order.args_schema.model_json_schema())
order_tool.py
    ---------------------------------------------------------------------------------------------------------------------------


import json
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import StateGraph, START, END
# from langgraph.prebuilt import ToolNode
from typing import Optional
# from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.checkpoint.postgres import PostgresSaver
# from src.database.repository import CustomerRepository
from src.services.customer_service import CustomerService
from src.database.order_repository import OrderRepository
from dotenv import load_dotenv
import os
load_dotenv()
postgres_uri = os.getenv("POSTGRES_URI")
# checkpointer = InMemorySaver()
from src.tools.order_tool import get_order
from langgraph.graph import MessagesState


class CustomerState(MessagesState):
    customer_id: str


# repo = CustomerRepository()
model = ChatOpenRouter(
    model="openrouter/free",
    temperature=0
)
tools = [get_order]
# tools_by_name = {
#     tool.name: tool
#     for tool in tools
# }
model_with_tools = model.bind_tools(tools)
# tool_node = ToolNode(tools)


# messages = [
#     HumanMessage(content="What is the status of order 12345?")
# ]
# response = model_with_tools.invoke(messages)
# messages.append(response)
# # print(response.tool_calls)
# tool_call = response.tool_calls[0]
# tool = tools_by_name[tool_call["name"]]

# tool_result = tool.invoke(tool_call["args"])
# messages.append(
#     ToolMessage(
#         content=str(tool_result),
#         tool_call_id=tool_call["id"]
#     )
# )
# final_response = model_with_tools.invoke(messages)

# print(final_response.content)
# def create_app():
#     checkpointer = InMemorySaver()
#     return graph.compile(checkpointer=checkpointer)

def call_model(state: CustomerState):
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def call_tools(state: CustomerState):
    last_message = state["messages"][-1]

    customer_id = state["customer_id"]

    # print("Customer ID from state:", customer_id)

    tool_call = last_message.tool_calls[0]

    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    order_id = str(tool_args["order_id"])

    order = order_repository.get_order(
    order_id,
    customer_id
    )

    # if order is None:
    #     result = {
    #         "order_id": order_id,
    #         "status": "not_found",
    #         "message": "Order not found for this customer"
    #     }
    # else:
    #     result = order

    # tool_message = ToolMessage(
    #     content=str(result),
    #     tool_call_id=tool_call["id"]
    # )

    # return {
    #     "messages": [tool_message]
    # }
    if order is None:
        result = {
        "order_id": order_id,
        "status": "not_found",
        "message": "Order not found for this customer"
    }
    else:
        result = {
        "order_id": order["order_id"],
        "status": order["status"],
        "dispatch_date": str(order["dispatch_date"]),
        "shipping_date": str(order["shipping_date"]),
        "receiving_date": str(order["receiving_date"])
    }

    tool_message = ToolMessage(
    content=json.dumps(result),
    tool_call_id=tool_call["id"]
)

    return {
    "messages": [tool_message]
}


def should_continue(state: MessagesState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"

# graph = StateGraph(MessagesState)
order_repository = OrderRepository()
graph = StateGraph(CustomerState)
graph.add_node("agent", call_model)
# graph.add_node("tools", tool_node)
graph.add_node("tools", call_tools)
graph.add_edge(START, "agent")
# graph.add_edge("agent", END)
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
graph.add_edge("tools", "agent")
with PostgresSaver.from_conn_string(postgres_uri) as checkpointer:

    checkpointer.setup()

    app = graph.compile(
        checkpointer=checkpointer
    )

    # customer_id = input("Customer ID: ")
    # # thread_id = input("Thread ID: ")
    # # customer = repo.get_or_create_customer(customer_id)
    # # conversation = repo.get_or_create_conversation(customer_id)
    # customer = service.get_or_create_customer(customer_id)
    # conversation = service.get_or_create_conversation(customer_id)

    # thread_id = conversation[2]

    # print(f"Conversation started for {thread_id}")
    customer_id = input("Customer ID: ")

    service = CustomerService()

    customer = service.get_or_create_customer(
    customer_id
)

    conversations = service.get_conversations(
    customer_id
)

    if conversations:
        print("\nYour conversations:")

        for i, conversation in enumerate(conversations, start=1):
            print(f"{i}. {conversation[2]}")

        print("0. Start a new conversation")

        choice = int(input("\nSelect conversation: "))

        if choice == 0:
            conversation = service.start_conversation(
               customer_id
        )
        else:
            conversation = service.select_conversation(
            customer_id,
            choice
        )

            if conversation is None:
                print("Invalid conversation selection.")
                exit()

    else:
        conversation = service.start_conversation(
        customer_id
    )

    thread_id = conversation[2]

    print(f"\nConversation started for {thread_id}")

    while True:
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        result = app.invoke(
            {
                "customer_id": customer_id,
                "messages": [
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            }
        )

        print("Assistant:", result["messages"][-1].content)
# app = create_app()
# app = graph.compile(checkpointer=checkpointer)
# result = app.invoke({
#     "messages": [
#         {
#             "role": "user",
#             "content": "What is the status of order 99999?"
#         }
#     ]
# })

# print(result["messages"][-1].content)
# user_input = input("You: ")

# result = app.invoke(
#     {
#         "messages": [
#             {
#                 "role": "user",
#                 "content": user_input
#             }
#         ]
#     },
#     config={
#         "configurable": {
#             "thread_id": "customer-001"
#         }
#     }
# )

# print("Assistant:", result["messages"][-1].content)
# thread_id = "customer-001"
# customer_id = input("Customer ID: ")
# thread_id = input("Thread ID: ")
# print(f"Conversation started for {thread_id}")

# while True:
#     user_input = input("You: ")

#     if user_input.lower() in ["exit", "quit"]:
#         print("Goodbye!")
#         break

#     result = app.invoke(
#         {
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": user_input
#                 }
#             ]
#         },
#         config={
#             "configurable": {
#                 "thread_id": thread_id
#             }
#         }
#     )

#     print("Assistant:", result["messages"][-1].content) agent.py
------------------------------------------------------------------
------------------------

