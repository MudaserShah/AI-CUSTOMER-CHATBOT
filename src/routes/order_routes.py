import logging

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from src.auth.dependencies import get_current_customer_id
from src.database.errors import DatabaseError
from src.rate_limit import limiter
from src.schemas.order_schemas import OrderResponse
from src.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])
order_service = OrderService()


@router.get("", response_model=list[OrderResponse])
@limiter.limit("30/minute")
def list_orders(
    request: Request,
    customer_id: str = Depends(get_current_customer_id),
):
    try:
        return order_service.list_orders(customer_id)
    except DatabaseError:
        logger.exception("Database error while listing orders for customer_id=%s", customer_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble loading your orders right now.",
        ) from None


@router.get("/{order_id}", response_model=OrderResponse)
@limiter.limit("30/minute")
def get_order(
    request: Request,
    order_id: str = Path(..., pattern=r"^[0-9]{5}$"),
    customer_id: str = Depends(get_current_customer_id),
):
    try:
        order = order_service.get_order(customer_id, order_id)
    except DatabaseError:
        logger.exception(
            "Database error while reading order: customer_id=%s order_id=%s",
            customer_id,
            order_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble loading that order right now.",
        ) from None

    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    return order
