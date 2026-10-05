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

verification_service = VerificationService()


@router.post("/token", response_model=TokenResponse)
def issue_token(request: TokenRequest):
    result = verification_service.verify_customer(
        customer_id=request.customer_id,
        provided_email=request.email,
    )

    if not result["verified"]:
        # Deliberately not logging the email they tried — it's PII and
        # of limited debugging value; customer_id + outcome is enough.
        logger.warning(
            "Token issuance rejected: customer_id=%s reason=%s",
            request.customer_id, result["reason"],
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result["reason"],
        )

    logger.info("Token issued: customer_id=%s", request.customer_id)

    token = create_access_token(customer_id=request.customer_id)

    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.jwt_expiry_minutes,
    )
