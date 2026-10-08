import logging
import secrets
import uuid
from decimal import Decimal

from psycopg.errors import UniqueViolation

from src.auth.jwt_utils import create_access_token
from src.database.order_repository import OrderRepository
from src.database.repository import CustomerRepository
from src.rag.config import settings
from src.schemas.store_schemas import CheckoutRequest
from src.store.catalog import get_product, list_products

logger = logging.getLogger(__name__)


class ExistingCustomerCheckoutError(Exception):
    """Raised when an unauthenticated checkout targets an existing account."""


class StoreService:
    """Checkout/application service for the demo ecommerce storefront."""

    def __init__(self, customer_repository=None, order_repository=None):
        self.customer_repository = customer_repository or CustomerRepository()
        self.order_repository = order_repository or OrderRepository()

    @staticmethod
    def _new_customer_id() -> str:
        return f"customer-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _new_order_id() -> str:
        return f"{secrets.randbelow(90000) + 10000:05d}"

    def _create_new_customer(self, name: str, email: str):
        try:
            return self.customer_repository.create_customer(
                customer_id=self._new_customer_id(),
                name=name.strip(),
                email=email.strip().lower(),
            )
        except UniqueViolation:
            # A unique lower(email) index is recommended for production.
            existing = self.customer_repository.get_customer_by_email(email)
            if existing:
                raise ExistingCustomerCheckoutError from None
            raise

    def _resolve_customer(self, payload: CheckoutRequest, authenticated_customer_id: str | None):
        normalized_email = str(payload.email).strip().lower()

        if authenticated_customer_id:
            customer = self.customer_repository.get_customer(authenticated_customer_id)
            if customer is None:
                raise ValueError("Authenticated customer account was not found.")
            if (customer[3] or "").lower() != normalized_email:
                raise ValueError("The signed-in email does not match this customer account.")
            return customer

        existing = self.customer_repository.get_customer_by_email(normalized_email)
        if existing:
            raise ExistingCustomerCheckoutError

        return self._create_new_customer(payload.name, normalized_email)

    def checkout(
        self,
        payload: CheckoutRequest,
        authenticated_customer_id: str | None = None,
    ) -> dict:
        customer = self._resolve_customer(payload, authenticated_customer_id)
        customer_id = customer[1]

        normalized_items = []
        total = Decimal("0.00")
        currencies = set()

        for requested_item in payload.items:
            product = get_product(requested_item.product_id)
            if product is None:
                raise ValueError(f"Product '{requested_item.product_id}' was not found.")

            quantity = requested_item.quantity
            unit_price = product["unit_price"]
            line_total = unit_price * quantity
            total += line_total
            currencies.add(product["currency"])
            normalized_items.append(
                {
                    "product_id": product["id"],
                    "name": product["name"],
                    "quantity": quantity,
                    "unit_price": str(unit_price),
                    "line_total": str(line_total),
                }
            )

        if len(currencies) != 1:
            raise ValueError("The checkout cart contains products with different currencies.")
        currency = currencies.pop()

        order = None
        for _ in range(12):
            try:
                order = self.order_repository.create_order(
                    order_id=self._new_order_id(),
                    customer_id=customer_id,
                    delivery_address=payload.delivery_address.strip(),
                    items=normalized_items,
                    total_amount=total,
                    currency=currency,
                    payment_method=payload.payment_method,
                )
                break
            except UniqueViolation:
                continue

        if order is None:
            raise RuntimeError("Could not allocate a unique order number.")

        access_token = create_access_token(customer_id=customer_id)

        logger.info(
            "Checkout completed: customer_id=%s order_id=%s total=%s",
            customer_id,
            order["order_id"],
            order["total_amount"],
        )

        return {
            "customer_id": customer_id,
            "order_id": order["order_id"],
            "status": order["status"],
            "name": customer[2],
            "email": customer[3],
            "delivery_address": order["delivery_address"],
            "items": normalized_items,
            "total_amount": total,
            "currency": currency,
            "payment_method": order["payment_method"],
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in_minutes": settings.jwt_expiry_minutes,
        }

    def products(self) -> list[dict]:
        return list_products()
