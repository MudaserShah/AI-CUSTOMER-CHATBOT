from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class CheckoutItem(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=80)
    quantity: int = Field(default=1, ge=1, le=20)


class CheckoutRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    delivery_address: str = Field(..., min_length=5, max_length=500)
    items: list[CheckoutItem] = Field(..., min_length=1, max_length=20)
    payment_method: Literal["cod"] = "cod"


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    unit_price: Decimal
    currency: str
    image_emoji: str


class CheckoutItemResponse(BaseModel):
    product_id: str
    name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal


class CheckoutResponse(BaseModel):
    customer_id: str
    order_id: str
    status: str
    name: str
    email: EmailStr
    delivery_address: str
    items: list[CheckoutItemResponse]
    total_amount: Decimal
    currency: str
    payment_method: str
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
