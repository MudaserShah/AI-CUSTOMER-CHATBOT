import os
import json
from langchain_openrouter import ChatOpenRouter
from langgraph.graph import StateGraph, START, END, MessagesState
from langchain_core.messages import ToolMessage, SystemMessage
from langgraph.checkpoint.postgres import PostgresSaver
from src.database.order_repository import OrderRepository
from dotenv import load_dotenv
from src.tools.order_tool import get_order
from src.tools.knowledge_tool import search_knowledge_base
from src.tools.refund_tool import create_refund_request
from src.tools.refund_status_tool import get_refund_status
from src.services.refund_service import RefundService
from src.tools.address_tool import change_delivery_address
from src.services.address_service import AddressService
load_dotenv()
postgres_uri = os.getenv("POSTGRES_URI")


class CustomerState(MessagesState):
    customer_id: str



model = ChatOpenRouter(
    model="openrouter/free",
    temperature=0
)
tools = [get_order, search_knowledge_base, create_refund_request, get_refund_status, change_delivery_address]

model_with_tools = model.bind_tools(tools)

SYSTEM_PROMPT = """
You are TechNest Electronics' customer support AI assistant.

Your job is to answer customers accurately using the available tools.

TOOLS:

1. get_order
- Use this when the customer asks about a specific order.
- The order ID must be exactly 5 digits.
- Use the tool result as the source of truth.
- Never invent order status, dates, or delivery information.

2. search_knowledge_base
- Use this for company policies, refunds, returns, delivery policies,
  product information, FAQs, warranty information, and other general
  customer-support questions.
- Use ONLY information returned by this tool.
- Never use outside knowledge.
3. create_refund_request

- Use this when the customer explicitly wants to request a refund.
- The order ID must be exactly 5 digits.
- The customer must provide a reason for the refund.
- Never invent a reason.
- Never ask the customer for their customer ID.
- Customer identity is handled internally by the system.
4. get_refund_status

- Use this when the customer asks about the status of an existing refund request.
- The order ID must be exactly 5 digits.
- Use the tool result as the source of truth.
- Never invent refund status.
- Never ask the customer for their customer ID.
- Customer identity is handled internally by the system.
5. change_delivery_address

- Use this when the customer explicitly wants to change their delivery address.
- The order ID must be exactly 5 digits.
- The customer must provide the new delivery address.
- Never ask the customer for their customer ID.
- Customer identity is handled internally by the system.
- Use the tool result as the source of truth.

GENERAL RULES:

- Answer only what the customer asked.
- Keep answers concise and directly relevant.
- Do not add unrelated policy information.
- Do not invent facts, dates, prices, statuses, or policies.
- If the required information is not available from the tools, say:
  "I couldn't find that information in our records."
  - Never create a refund request without a valid 5-digit order ID and a customer-provided reason.

ORDER RULES:

- If the customer provides an order ID, use get_order.
- If the order ID is not exactly 5 digits, ask the customer for their
  5-digit order number.
- Do not guess or modify an order ID.
- Do not remove "#" or any other characters from an order ID.
- "12345" is valid.
- "#12345" is invalid.
- "123" is invalid.
- "ABCDE" is invalid.
ADDRESS CHANGE RULES:

- If the customer wants to change their delivery address, use change_delivery_address.
- The order ID must be exactly 5 digits.
- The new address must be provided by the customer.
- Do not guess or modify the order ID.
- Do not change the address of an order belonging to another customer.
- If the order has already been delivered, the address cannot be changed.
- The customer must provide the email associated with their account for identity verification.
- If the customer has not provided their email, ask them for the email associated with their account before calling the tool.

KNOWLEDGE BASE RULES:

- For questions about TechNest policies or information, use
  search_knowledge_base before answering.
- Treat the knowledge-base result as the source of truth.
- Do not add information that was not returned by the tool.

RESPONSE STYLE:

- Be professional and helpful.
- Answer the exact question first.
- Do not unnecessarily repeat information.
- Do not mention internal tools, Qdrant, embeddings, retrieval,
  prompts, or system instructions.
"""


def call_model(state: CustomerState):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = model_with_tools.invoke(messages)

    return {
        "messages": [response]
    }

#

def call_tools(state: CustomerState):
    last_message = state["messages"][-1]

    tool_messages = []

    # for tool_call in last_message.tool_calls:
    tool_calls = (
    last_message.tool_calls
    if hasattr(last_message, "tool_calls")
    else last_message["tool_calls"]
)

    for tool_call in tool_calls:

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name == "get_order":

            order_id = str(
                tool_args["order_id"]
            )

            customer_id = state["customer_id"]

            order = order_repository.get_order(
                order_id,
                customer_id
            )

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
                    "receiving_date": str(order["receiving_date"]),
                    "delivery_address": order["delivery_address"],

                }

            tool_messages.append(
                ToolMessage(
                    content=json.dumps(result),
                    tool_call_id=tool_call["id"]
                )
            )

        elif tool_name == "search_knowledge_base":

            result = search_knowledge_base.invoke(
                tool_args
            )

            tool_messages.append(
                ToolMessage(
                    content=result,
                    tool_call_id=tool_call["id"]
                )
            )
    
        elif tool_name == "create_refund_request":

           order_id = str(
        tool_args["order_id"]
    )

           reason = tool_args["reason"]

           customer_id = state["customer_id"]

           result = refund_service.create_refund_request(
        customer_id=customer_id,
        order_id=order_id,
        reason=reason,
    )

           tool_messages.append(
        ToolMessage(
            content=json.dumps(result),
            tool_call_id=tool_call["id"]
        )
    )

        elif tool_name == "get_refund_status":

            order_id = str(
        tool_args["order_id"]
    )

            customer_id = state["customer_id"]

            refund_status = refund_service.get_refund_status(
        customer_id=customer_id,
        order_id=order_id,
    )

            if refund_status is None:

                result = {
            "status": "not_found",
            "order_id": order_id,
            "message": (
                "No refund request was found "
                "for this order."
            )
        }

            else:

               result = {
            "status": "found",
            "refund_request_id": refund_status["id"],
            "order_id": refund_status["order_id"],
            "refund_status": refund_status["status"],
            "reason": refund_status["reason"],
            "created_at": str(
                refund_status["created_at"]
            )
        }

            tool_messages.append(
        ToolMessage(
            content=json.dumps(result),
            tool_call_id=tool_call["id"]
        )
    )

        elif tool_name == "change_delivery_address":

            order_id = str(
        tool_args["order_id"]
    )

            new_address = tool_args["new_address"]
            provided_email = tool_args["provided_email"]

            customer_id = state["customer_id"]

            result = address_service.change_delivery_address(
        customer_id=customer_id,
        order_id=order_id,
        new_address=new_address,
        provided_email=provided_email,
    )

            tool_messages.append(
        ToolMessage(
            content=json.dumps(result),
            tool_call_id=tool_call["id"]
        )
    )
    return {
        "messages": tool_messages
    }



def should_continue(state: MessagesState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


order_repository = OrderRepository()
refund_service = RefundService()
address_service = AddressService()
graph = StateGraph(CustomerState)
graph.add_node("agent", call_model)
graph.add_node("tools", call_tools)
graph.add_edge(START, "agent")
graph.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
graph.add_edge("tools", "agent")

checkpointer_cm = PostgresSaver.from_conn_string(postgres_uri)
checkpointer = checkpointer_cm.__enter__()
checkpointer.setup()

app = graph.compile(
        checkpointer=checkpointer
    )

