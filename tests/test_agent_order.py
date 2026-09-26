from src.agent.agent import call_tools


def test_agent_order_tool_passes_customer_context():

    import src.agent.agent as agent_module

    class FakeOrderRepository:

        def get_order(self, order_id, customer_id):

            assert order_id == "12345"
            assert customer_id == "customer-001"

            return {
                "order_id": "12345",
                "status": "Shipped",
                "dispatch_date": "2026-09-14",
                "shipping_date": "2026-09-15",
                "receiving_date": "2026-09-19",
                "delivery_address": "Wah Cantt",
            }

    agent_module.order_repository = FakeOrderRepository()

    state = {
        "customer_id": "customer-001",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "get_order",
                        "args": {
                            "order_id": "12345",
                        },
                        "id": "tool-call-order-001",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-order-001"
    assert "12345" in tool_message.content
    assert "Shipped" in tool_message.content
    assert "2026-09-14" in tool_message.content
    assert "2026-09-15" in tool_message.content
    assert "2026-09-19" in tool_message.content