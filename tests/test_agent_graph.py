from langchain_core.messages import AIMessage

import src.agent.agent as agent_module

# class FakeModel:

#     def invoke(self, messages):

#         from langchain_core.messages import AIMessage

#         return AIMessage(
#             content="",
#             tool_calls=[
#                 {
#                     "name": "create_refund_request",
#                     "args": {
#                         "order_id": "12348",
#                         "reason": "Product is defective",
#                     },
#                     "id": "integration-refund-001",
#                 }
#             ],
#         )
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
                        "id": "integration-refund-001",
                    }
                ],
            )

        return AIMessage(
            content="Your refund request has been submitted successfully."
        )

def test_agent_graph_refund_flow():

    import src.agent.agent as agent_module

    agent_module.model_with_tools = FakeModel()

    state = {
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
}
    result = agent_module.call_model(state)
    response = result["messages"][-1]
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0]["name"] == "create_refund_request"
    assert response.tool_calls[0]["args"]["order_id"] == "12348"
    assert response.tool_calls[0]["args"]["reason"] == "Product is defective"

    tool_result = agent_module.call_tools({
    "customer_id": "customer-002",
    "messages": result["messages"],
})
    assert len(tool_result["messages"]) == 1
    final_result = agent_module.call_model({
        "customer_id": "customer-002",
        "messages": result["messages"] + tool_result["messages"],
    })

    final_response = final_result["messages"][-1]

    assert final_response.content