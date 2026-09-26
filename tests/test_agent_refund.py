from src.agent.agent import call_tools


class FakeRefundService:

    def create_refund_request(
        self,
        customer_id,
        order_id,
        reason,
    ):
        return {
            "status": "submitted",
            "refund_request_id": "test-refund-001",
            "order_id": order_id,
            "reason": reason,
            "refund_status": "pending",
        }


def test_agent_refund_tool_passes_customer_context():

    # Arrange
    import src.agent.agent as agent_module

    agent_module.refund_service = FakeRefundService()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12348",
                            "reason": "Product is defective",
                        },
                        "id": "tool-call-001",
                    }
                ],
            }
        ],
    }

    # Act
    result = call_tools(state)

    # Assert
    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-001"

    assert "customer-002" not in tool_message.content
    assert "12348" in tool_message.content
    assert "Product is defective" in tool_message.content
    assert "test-refund-001" in tool_message.content
class FakeRefundServiceRejected:

    def create_refund_request(
        self,
        customer_id,
        order_id,
        reason,
    ):
        return {
            "status": "rejected",
            "order_id": order_id,
            "reason": "Order has not been delivered yet.",
        }


def test_agent_refund_tool_handles_rejected_refund():

    import src.agent.agent as agent_module

    agent_module.refund_service = FakeRefundServiceRejected()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12346",
                            "reason": "Product is defective",
                        },
                        "id": "tool-call-002",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-002"
    assert "rejected" in tool_message.content
    assert "12346" in tool_message.content
    assert "Order has not been delivered yet." in tool_message.content

def test_agent_refund_order_not_delivered():

    import src.agent.agent as agent_module

    class FakeRefundServiceNotDelivered:

        def create_refund_request(
            self,
            customer_id,
            order_id,
            reason,
        ):
            return {
                "status": "rejected",
                "order_id": order_id,
                "reason": "Order has not been delivered yet.",
            }

    agent_module.refund_service = FakeRefundServiceNotDelivered()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12346",
                            "reason": "Product is defective",
                        },
                        "id": "tool-call-002",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-002"
    assert "rejected" in tool_message.content
    assert "Order has not been delivered yet." in tool_message.content

def test_agent_refund_already_exists():

    import src.agent.agent as agent_module

    class FakeRefundServiceAlreadyExists:

        def create_refund_request(
            self,
            customer_id,
            order_id,
            reason,
        ):
            return {
                "status": "already_exists",
                "refund_request_id": "existing-refund-123",
                "order_id": order_id,
                "refund_status": "pending",
            }

    agent_module.refund_service = FakeRefundServiceAlreadyExists()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12348",
                            "reason": "Product is defective",
                        },
                        "id": "tool-call-003",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-003"
    assert "already_exists" in tool_message.content
    assert "existing-refund-123" in tool_message.content

def test_agent_model_requests_refund_tool():

    import src.agent.agent as agent_module

    class FakeModelWithTools:

        def invoke(self, messages):

            from langchain_core.messages import AIMessage

            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12348",
                            "reason": "Product is defective",
                        },
                        "id": "tool-call-model-001",
                    }
                ],
            )

    agent_module.model_with_tools = FakeModelWithTools()

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

    assert len(result["messages"]) == 1

    response = result["messages"][0]

    assert len(response.tool_calls) == 1

    tool_call = response.tool_calls[0]

    assert tool_call["name"] == "create_refund_request"
    assert tool_call["args"]["order_id"] == "12348"
    assert tool_call["args"]["reason"] == "Product is defective"

def test_agent_refund_end_to_end():

    import src.agent.agent as agent_module

    from langchain_core.messages import AIMessage

    class FakeRefundService:

        def create_refund_request(
            self,
            customer_id,
            order_id,
            reason,
        ):
            assert customer_id == "customer-002"
            assert order_id == "12348"
            assert reason == "Product is defective"

            return {
                "status": "submitted",
                "refund_request_id": "e2e-refund-001",
                "order_id": order_id,
                "reason": reason,
                "refund_status": "pending",
            }

    class FakeModel:

        def invoke(self, messages):

            return AIMessage(
                content="Refund request submitted successfully.",
            )

    agent_module.refund_service = FakeRefundService()

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

    # First model call
    class FakeModelWithToolCall:

        def invoke(self, messages):

            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "create_refund_request",
                        "args": {
                            "order_id": "12348",
                            "reason": "Product is defective",
                        },
                        "id": "e2e-tool-call-001",
                    }
                ],
            )

    agent_module.model_with_tools = FakeModelWithToolCall()

    model_result = agent_module.call_model(state)

    assert len(model_result["messages"]) == 1

    assistant_message = model_result["messages"][0]

    assert assistant_message.tool_calls[0]["name"] == (
        "create_refund_request"
    )

    # Tool execution
    tool_state = {
        "customer_id": "customer-002",
        "messages": [
            assistant_message
        ],
    }

    tool_result = agent_module.call_tools(tool_state)

    assert len(tool_result["messages"]) == 1

    tool_message = tool_result["messages"][0]

    assert tool_message.tool_call_id == "e2e-tool-call-001"
    assert "submitted" in tool_message.content
    assert "e2e-refund-001" in tool_message.content