from pydantic import BaseModel, Field


class RefundRequest(BaseModel):
    order_id: str = Field(..., pattern=r"^[0-9]{5}$", description="5-digit order identifier")
    reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Reason for requesting a refund",
    )


class RefundResponse(BaseModel):
    status: str
    order_id: str | None = None
    refund_status: str | None = None
    refund_request_id: str | None = None
    reason: str | None = None
    message: str | None = None
    created_at: str | None = None
