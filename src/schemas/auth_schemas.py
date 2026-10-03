from pydantic import BaseModel, Field


class TokenRequest(BaseModel):

    customer_id: str = Field(
        ...,
        description="Unique customer identifier",
    )

    email: str = Field(
        ...,
        description="Email on file for this customer, used to prove identity",
    )


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
