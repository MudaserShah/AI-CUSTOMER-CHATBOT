from datetime import datetime, timedelta, timezone

import jwt
import pytest

from src.auth.jwt_utils import (
    InvalidTokenError,
    create_access_token,
    decode_access_token,
)
from src.rag.config import settings


def test_create_and_decode_access_token():
    customer_id = "customer-test-001"

    token = create_access_token(customer_id)

    assert isinstance(token, str)
    assert decode_access_token(token) == customer_id


def test_decode_rejects_expired_token():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "customer-test-001",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError, match="expired"):
        decode_access_token(token)


def test_decode_rejects_wrong_signature():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "customer-test-001",
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        "wrong-secret",
        algorithm="HS256",
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_rejects_missing_sub():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    with pytest.raises(
        InvalidTokenError,
        match="missing.*sub",
    ):
        decode_access_token(token)


def test_decode_rejects_malformed_token():
    with pytest.raises(InvalidTokenError):
        decode_access_token("not-a-real-jwt")
