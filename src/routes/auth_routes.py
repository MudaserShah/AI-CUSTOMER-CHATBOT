"""
NOTE on this route's role in the architecture:

In a real deployment, this chatbot sits behind a host application
(the e-commerce site) that already knows who is logged in. That host
app should mint the JWT itself and hand it to the chat widget — this
service would then only ever *verify* tokens, never issue them.

This endpoint exists so the project can be run and tested end to end
without building that separate host application. It reuses the same
identity check (customer_id + email on file) that VerificationService
already uses for the address-change flow, so "proving you are the
customer" is based on the same standard everywhere in this codebase.
"""
import logging

from fastapi import APIRouter, HTTPException, status

from src.auth.jwt_utils import create_access_token
from src.rag.config import settings
from src.schemas.auth_schemas import TokenRequest, TokenResponse
from src.services.verification_service import VerificationService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

from src.database.repository import CustomerRepository

verification_service = VerificationService()
customer_repo = CustomerRepository()


@router.post("/token", response_model=TokenResponse)
def issue_token(request: TokenRequest):
    target_customer_id = request.customer_id
    customer_name = None

    if not target_customer_id:
        record = customer_repo.get_customer_by_email(request.email)
        if not record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No customer found with this email address.",
            )
        target_customer_id = record[1]
        customer_name = record[2]
    else:
        result = verification_service.verify_customer(
            customer_id=target_customer_id,
            provided_email=request.email,
        )
        if not result["verified"]:
            logger.warning(
                "Token issuance rejected: customer_id=%s reason=%s",
                target_customer_id, result["reason"],
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result["reason"],
            )
        record = customer_repo.get_customer(target_customer_id)
        if record:
            customer_name = record[2]

    logger.info("Token issued: customer_id=%s", target_customer_id)

    token = create_access_token(customer_id=target_customer_id)

    return TokenResponse(
        access_token=token,
        customer_id=target_customer_id,
        name=customer_name or "Customer",
        email=request.email,
        expires_in_minutes=settings.jwt_expiry_minutes,
    )

