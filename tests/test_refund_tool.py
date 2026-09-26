from src.tools.refund_tool import create_refund_request


def test_create_refund_request_tool():

    result = create_refund_request.invoke({
        "order_id": "12345",
        "reason": "Product is defective",
    })

    assert result["order_id"] == "12345"
    assert result["reason"] == "Product is defective"
    assert result["status"] == "ready_for_submission"