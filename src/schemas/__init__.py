from pydantic import BaseModel, Field


class RefundRequest(BaseModel):

    customer_id: str = Field(
        ...,
        description="Unique customer identifier",
    )

    order_id: str = Field(
        ...,
        min_length=5,
        max_length=5,
        description="5-digit order identifier",
    )

    reason: str = Field(
        ...,
        min_length=1,
        description="Reason for requesting a refund",
    )


class RefundResponse(BaseModel):

    status: str

    order_id: str

    refund_status: str | None = None

    refund_request_id: str | None = None

    reason: str | None = None

    message: str | None = None