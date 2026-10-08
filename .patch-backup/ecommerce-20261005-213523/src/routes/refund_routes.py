import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.dependencies import get_current_customer_id
from src.database.errors import DatabaseError
from src.rate_limit import limiter
from src.schemas.refund_schemas import (
    RefundRequest,
    RefundResponse,
)

from src.services.refund_service import RefundService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/refund",
    tags=["Refund"],
)


refund_service = RefundService()


@router.post(
    "",
    response_model=RefundResponse,
)
@limiter.limit("10/minute")
def create_refund(
    request: Request,
    body: RefundRequest,
    customer_id: str = Depends(get_current_customer_id),
):
    try:
        return refund_service.create_refund_request(
            customer_id=customer_id,
            order_id=body.order_id,
            reason=body.reason,
        )
    except DatabaseError:
        logger.exception("Database error while creating refund for customer_id=%s", customer_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble reaching our systems right now. Please try again shortly.",
        )

@router.get(
    "/{order_id}",
    response_model=RefundResponse,
)
@limiter.limit("30/minute")
def get_refund_status(
    request: Request,
    order_id: str,
    customer_id: str = Depends(get_current_customer_id),
):
    try:
        result = refund_service.get_refund_status(
            customer_id=customer_id,
            order_id=order_id,
        )
    except DatabaseError:
        logger.exception("Database error while fetching refund status for customer_id=%s", customer_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble reaching our systems right now. Please try again shortly.",
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