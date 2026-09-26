from src.agent.agent import call_tools


class FakeAddressService:

    def change_delivery_address(
        self,
        customer_id,
        order_id,
        new_address,
        provided_email,
    ):
        assert customer_id == "customer-002"

        return {
            "status": "updated",
            "order_id": order_id,
            "delivery_address": new_address,
        }


def test_agent_address_tool_passes_customer_context():

    import src.agent.agent as agent_module

    agent_module.address_service = FakeAddressService()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "change_delivery_address",
                        "args": {
                            "order_id": "12346",
                            "new_address": "House 500, Street 20, Wah Cantt",
                            "provided_email": "ahmed@example.com",
                        },
                        "id": "tool-call-address-001",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-address-001"

    assert "updated" in tool_message.content
    assert "12346" in tool_message.content
    assert "House 500, Street 20, Wah Cantt" in tool_message.content

class FakeAddressServiceRejected:

    def change_delivery_address(
        self,
        customer_id,
        order_id,
        new_address,
        provided_email,
    ):
        return {
            "status": "rejected",
            "order_id": order_id,
            "reason": "Customer verification failed.",
        }


def test_agent_address_tool_handles_verification_failure():

    import src.agent.agent as agent_module

    agent_module.address_service = FakeAddressServiceRejected()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "change_delivery_address",
                        "args": {
                            "order_id": "12346",
                            "new_address": "House 500, Street 20, Wah Cantt",
                            "provided_email": "wrong@example.com",
                        },
                        "id": "tool-call-address-002",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-address-002"
    assert "rejected" in tool_message.content
    assert "12346" in tool_message.content
    assert "Customer verification failed." in tool_message.content

class FakeAddressServiceDelivered:

    def change_delivery_address(
        self,
        customer_id,
        order_id,
        new_address,
        provided_email,
    ):
        return {
            "status": "rejected",
            "order_id": order_id,
            "reason": (
                "Delivery address cannot be changed "
                "after the order is delivered."
            ),
        }


def test_agent_address_tool_rejects_delivered_order():

    import src.agent.agent as agent_module

    agent_module.address_service = FakeAddressServiceDelivered()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "change_delivery_address",
                        "args": {
                            "order_id": "12348",
                            "new_address": "House 500, Street 20, Wah Cantt",
                            "provided_email": "ahmed@example.com",
                        },
                        "id": "tool-call-address-003",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-address-003"
    assert "rejected" in tool_message.content
    assert "12348" in tool_message.content
    assert (
        "Delivery address cannot be changed "
        "after the order is delivered."
        in tool_message.content
    )

class FakeAddressServiceUpdated:

    def change_delivery_address(
        self,
        customer_id,
        order_id,
        new_address,
        provided_email,
    ):
        return {
            "status": "updated",
            "order_id": order_id,
            "delivery_address": new_address,
        }


def test_agent_address_tool_updates_address():

    import src.agent.agent as agent_module

    agent_module.address_service = FakeAddressServiceUpdated()

    state = {
        "customer_id": "customer-002",
        "messages": [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "name": "change_delivery_address",
                        "args": {
                            "order_id": "12346",
                            "new_address": "House 500, Street 20, Wah Cantt",
                            "provided_email": "ahmed@example.com",
                        },
                        "id": "tool-call-address-004",
                    }
                ],
            }
        ],
    }

    result = call_tools(state)

    assert len(result["messages"]) == 1

    tool_message = result["messages"][0]

    assert tool_message.tool_call_id == "tool-call-address-004"
    assert "updated" in tool_message.content
    assert "12346" in tool_message.content
    assert "House 500, Street 20, Wah Cantt" in tool_message.content