from langchain_core.messages import AIMessage

import src.agent.agent as agent_module


class FakeModel:

    def __init__(self):
        self.calls = 0

    def invoke(self, messages):

        self.calls += 1

        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12348",
                            "reason": "Product is defective",
                        },
                        "id": "compiled-refund-001",
                    }
                ],
            )

        return AIMessage(
            content="Your refund request has been submitted successfully."
        )


def test_compiled_graph_refund_flow():

    agent_module.model_with_tools = FakeModel()

    result = agent_module.app.invoke(
        {
            "customer_id": "customer-002",
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "I want a refund for order 12348 "
                        "because the product is defective."
                    ),
                }
            ],
        },
        config={
            "configurable": {
                "thread_id": "test-compiled-refund-001"
            }
        },
    )

    final_response = result["messages"][-1]

    assert final_response.content
    assert (
        final_response.content
        == "Your refund request has been submitted successfully."
    )