"""
FastAPI dependency for authenticated routes.

Usage in a route:

    @router.post("")
    def chat(request: ChatRequest, customer_id: str = Depends(get_current_customer_id)):
        ...

customer_id no longer comes from the request body/query string — it is
derived from a verified JWT in the Authorization header. A route that
depends on get_current_customer_id cannot be called successfully
without a valid token, and the customer_id it receives cannot be
spoofed by the caller.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt_utils import InvalidTokenError, decode_access_token

_bearer_scheme = HTTPBearer(
    scheme_name="BearerAuth",
    description="Paste the access token obtained from POST /auth/token",
)


def get_current_customer_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> str:
    try:
        return decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
