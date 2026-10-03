import psycopg
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid

from src.database.db_utils import handle_db_errors
from src.database.pool import get_pool

class OrderRepository:

    def __init__(self, connection_uri: Optional[str] = None):
        self._override_uri = connection_uri

    def _get_connection(self):
        if self._override_uri:
            return psycopg.connect(self._override_uri)
        return get_pool().connection()

    @handle_db_errors
    def get_order(self, order_id, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                    order_id,
                    customer_id,
                    status,
                    dispatch_date,
                    shipping_date,
                    receiving_date,
                    delivered_at,
                    delivery_address
                    FROM orders
                    WHERE order_id = %s
                    AND customer_id = %s;
                    """,
                    (order_id, customer_id)
                )
                          
                row = cur.fetchone()

                if row is None:
                    return None

                return {
                "order_id": row[0],
                "customer_id": row[1],
                "status": row[2],
                "dispatch_date": row[3],
                "shipping_date": row[4],
                "receiving_date": row[5],
                "delivered_at": row[6],
                "delivery_address": row[7],
                }

    @handle_db_errors
    def update_delivery_address(
    self,
    order_id: str,
    customer_id: str,
    new_address: str,
):
        with self._get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute(
                """
                UPDATE orders
                SET delivery_address = %s
                WHERE order_id = %s
                AND customer_id = %s
                RETURNING
                    order_id,
                    customer_id,
                    delivery_address;
                """,
                (
                    new_address,
                    order_id,
                    customer_id,
                ),
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
                SELECT
                    order_id,
                    customer_id,
                    status,
                    delivered_at
                FROM orders
                WHERE order_id = %s
                AND customer_id = %s;
                """,
                (order_id, customer_id)
            )

                row = cur.fetchone()

                if row is None:
                    return {
                    "eligible": False,
                    "reason": "Order not found for this customer."
                }

                order_id = row[0]
                customer_id = row[1]
                status = row[2]
                delivered_at = row[3]

                if status != "Delivered":
                    return {
                    "eligible": False,
                    "reason": "Order has not been delivered yet."
                }

                if delivered_at is None:
                    return {
                    "eligible": False,
                    "reason": "Delivery date is not available."
                }

                refund_deadline = delivered_at + timedelta(days=7)

                now = datetime.now(timezone.utc)

                if now > refund_deadline:
                    return {
        "eligible": False,
        "reason": "The 7-day refund window has expired.",
        "refund_deadline": refund_deadline.isoformat()
    }

                return {
                "eligible": True,
                "order_id": order_id,
                "customer_id": customer_id,
                "status": status,
                "delivered_at": delivered_at.isoformat(),
                "refund_deadline": refund_deadline.isoformat()
            }

    
            


if __name__ == "__main__":
    repo = OrderRepository()

    order = repo.get_order(
    "12345",
    "customer-002"
)

    print(order)