"""
Minimal JWT issuing/verification helpers.

In production, the token handed to this service's clients should be
minted by whatever system already authenticates the customer (e.g.
the e-commerce site's own login). This service only needs to be able
to *verify* a token and trust its `sub` (subject) claim as the real,
authenticated customer_id.

create_access_token() is provided so this project can be tested end
to end without a separate host application — see src/routes/auth_routes.py
for the one place it's used.
"""
from datetime import datetime, timedelta, timezone

import jwt

from src.rag.config import settings

ALGORITHM = "HS256"


def create_access_token(customer_id: str) -> str:
    """Issue a signed JWT whose subject (sub) is the customer_id."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": customer_id,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


class InvalidTokenError(Exception):
    """Raised when a token is missing, malformed, expired, or has a bad signature."""


def decode_access_token(token: str) -> str:
    """Verify a JWT and return the customer_id (sub claim) it was issued for.

    Raises InvalidTokenError for any problem — expired, tampered,
    wrong signature, or missing the expected claim. The caller (the
    FastAPI dependency) turns this into a 401 response.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    customer_id = payload.get("sub")
    if not customer_id:
        raise InvalidTokenError("Token is missing the 'sub' (customer_id) claim.")

    return customer_id
