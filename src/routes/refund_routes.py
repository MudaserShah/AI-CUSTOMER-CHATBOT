from fastapi import APIRouter

from src.schemas.refund_schemas import (
    RefundRequest,
    RefundResponse,
)

from src.services.refund_service import RefundService


router = APIRouter(
    prefix="/refund",
    tags=["Refund"],
)


refund_service = RefundService()


@router.post(
    "",
    response_model=RefundResponse,
)
def create_refund(
    request: RefundRequest,
):
    return refund_service.create_refund_request(
        customer_id=request.customer_id,
        order_id=request.order_id,
        reason=request.reason,
    )

@router.get(
    "/{order_id}",
    response_model=RefundResponse,
)
def get_refund_status(
    order_id: str,
    customer_id: str,
):
    result = refund_service.get_refund_status(
        customer_id=customer_id,
        order_id=order_id,
    )

    if result is None:
        return {
            "status": "not_found",
            "order_id": order_id,
            "message": "No refund request was found for this order.",
        }

    return {
        "status": "found",
        "order_id": result["order_id"],
        "refund_status": result["status"],
        "refund_request_id": result["id"],
        "reason": result["reason"],
        "created_at": str(result["created_at"]),
    }