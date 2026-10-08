from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OrderResponse(BaseModel):
    order_id: str
    status: str
    delivery_address: str | None = None
    created_at: datetime | None = None
    dispatch_date: datetime | None = None
    shipping_date: datetime | None = None
    receiving_date: datetime | None = None
    delivered_at: datetime | None = None
    items: list[dict] = Field(default_factory=list)
    total_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    payment_method: str = "cod"
    refund_eligible: bool = False
    refund_reason: str | None = None
    refund_deadline: str | None = None
    refund_status: str | None = None
    refund_request_id: str | None = None
