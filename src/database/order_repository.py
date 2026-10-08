from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb

from src.database.base_repository import BaseRepository
from src.database.db_utils import handle_db_errors


class OrderRepository(BaseRepository):
    @staticmethod
    def _map_order(row):
        return {
            "order_id": row[0],
            "customer_id": row[1],
            "status": row[2],
            "dispatch_date": row[3],
            "shipping_date": row[4],
            "receiving_date": row[5],
            "delivered_at": row[6],
            "delivery_address": row[7],
            "created_at": row[8],
            "items": row[9] or [],
            "total_amount": row[10] or 0,
            "currency": row[11] or "USD",
            "payment_method": row[12] or "cod",
        }

    @handle_db_errors
    def create_order(
        self,
        order_id: str,
        customer_id: str,
        delivery_address: str,
        items: list[dict],
        total_amount,
        currency: str,
        payment_method: str,
    ):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO orders (
                        order_id, customer_id, status, delivery_address,
                        items, total_amount, currency, payment_method
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING
                        order_id, customer_id, status, dispatch_date,
                        shipping_date, receiving_date, delivered_at,
                        delivery_address, created_at, items, total_amount,
                        currency, payment_method;
                    """,
                    (
                        order_id,
                        customer_id,
                        "Processing",
                        delivery_address,
                        Jsonb(items),
                        total_amount,
                        currency,
                        payment_method,
                    ),
                )
                return self._map_order(cur.fetchone())

    @handle_db_errors
    def get_order(self, order_id, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        order_id, customer_id, status, dispatch_date,
                        shipping_date, receiving_date, delivered_at,
                        delivery_address, created_at, items, total_amount,
                        currency, payment_method
                    FROM orders
                    WHERE order_id = %s
                    AND customer_id = %s;
                    """,
                    (order_id, customer_id),
                )
                row = cur.fetchone()
                return None if row is None else self._map_order(row)

    @handle_db_errors
    def get_customer_orders(self, customer_id: str):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        order_id, customer_id, status, dispatch_date,
                        shipping_date, receiving_date, delivered_at,
                        delivery_address, created_at, items, total_amount,
                        currency, payment_method
                    FROM orders
                    WHERE customer_id = %s
                    ORDER BY created_at DESC, order_id DESC;
                    """,
                    (customer_id,),
                )
                return [self._map_order(row) for row in cur.fetchall()]

    @handle_db_errors
    def update_delivery_address(self, order_id: str, customer_id: str, new_address: str):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE orders
                    SET delivery_address = %s
                    WHERE order_id = %s
                    AND customer_id = %s
                    RETURNING order_id, customer_id, delivery_address;
                    """,
                    (new_address, order_id, customer_id),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return {
                    "order_id": row[0],
                    "customer_id": row[1],
                    "delivery_address": row[2],
                }

    @handle_db_errors
    def get_refund_eligibility(self, order_id, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT order_id, customer_id, status, delivered_at
                    FROM orders
                    WHERE order_id = %s
                    AND customer_id = %s;
                    """,
                    (order_id, customer_id),
                )
                row = cur.fetchone()

                if row is None:
                    return {"eligible": False, "reason": "Order not found for this customer."}

                status = row[2]
                delivered_at = row[3]

                if status != "Delivered":
                    return {"eligible": False, "reason": "Order has not been delivered yet."}

                if delivered_at is None:
                    return {"eligible": False, "reason": "Delivery date is not available."}

                refund_deadline = delivered_at + timedelta(days=7)
                now = datetime.now(timezone.utc)

                if now > refund_deadline:
                    return {
                        "eligible": False,
                        "reason": "The 7-day refund window has expired.",
                        "refund_deadline": refund_deadline.isoformat(),
                    }

                return {
                    "eligible": True,
                    "order_id": row[0],
                    "customer_id": row[1],
                    "status": status,
                    "delivered_at": delivered_at.isoformat(),
                    "refund_deadline": refund_deadline.isoformat(),
                }
