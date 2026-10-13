from typing import Optional
from pydantic import BaseModel, Field


class TokenRequest(BaseModel):

    customer_id: Optional[str] = Field(
        default=None,
        description="Unique customer identifier (optional if email is provided)",
    )

    email: str = Field(
        ...,
        description="Email on file for this customer, used to prove identity",
    )


class TokenResponse(BaseModel):

    access_token: str
    customer_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    token_type: str = "bearer"
    expires_in_minutes: int

