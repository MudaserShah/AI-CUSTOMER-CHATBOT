import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.auth.dependencies import get_optional_current_customer_id
from src.database.errors import DatabaseError
from src.rate_limit import limiter
from src.schemas.store_schemas import CheckoutRequest, CheckoutResponse, ProductResponse
from src.services.store_service import ExistingCustomerCheckoutError, StoreService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/store", tags=["Store"])
store_service = StoreService()


@router.get("/products", response_model=list[ProductResponse])
def get_products():
    return store_service.products()


@router.post("/checkout", response_model=CheckoutResponse)
@limiter.limit("20/minute")
def checkout(
    request: Request,
    body: CheckoutRequest,
    customer_id: str | None = Depends(get_optional_current_customer_id),
):
    try:
        return store_service.checkout(body, authenticated_customer_id=customer_id)
    except ExistingCustomerCheckoutError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this email. Please sign in before placing another order.",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DatabaseError:
        logger.exception("Database error during checkout")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We're having trouble completing your order right now. Please try again shortly.",
        ) from None
    except RuntimeError:
        logger.exception("Order-number allocation failed during checkout")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not allocate an order number. Please try again.",
        ) from None
