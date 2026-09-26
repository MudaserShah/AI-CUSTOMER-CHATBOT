import os
import uuid

import psycopg
from dotenv import load_dotenv

load_dotenv()


POSTGRES_URI = os.getenv("POSTGRES_URI")


class RefundRepository:

    def get_existing_refund(
    self,
    customer_id: str,
    order_id: str,
):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:

                cur.execute(
                """
                SELECT
                    id,
                    customer_id,
                    order_id,
                    reason,
                    status,
                    created_at
                FROM refund_requests
                WHERE customer_id = %s
                AND order_id = %s
                AND status IN ('pending', 'approved');
                """,
                (
                    customer_id,
                    order_id,
                ),
            )

                row = cur.fetchone()

                if row is None:
                    return None

                return {
                "id": str(row[0]),
                "customer_id": row[1],
                "order_id": row[2],
                "reason": row[3],
                "status": row[4],
                "created_at": row[5],
            }

    def __init__(self, connection_uri=POSTGRES_URI):
        self.database_url = connection_uri

    def create_refund_request(
        self,
        customer_id: str,
        order_id: str,
        reason: str,
    ):
        refund_id = uuid.uuid4()

        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO refund_requests (
                        id,
                        customer_id,
                        order_id,
                        reason,
                        status
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING
                        id,
                        customer_id,
                        order_id,
                        reason,
                        status,
                        created_at;
                    """,
                    (
                        refund_id,
                        customer_id,
                        order_id,
                        reason,
                        "pending",
                    ),
                )

                row = cur.fetchone()

                return {
                    "id": str(row[0]),
                    "customer_id": row[1],
                    "order_id": row[2],
                    "reason": row[3],
                    "status": row[4],
                    "created_at": row[5],
                }

    def get_refund_status(
    self,
    customer_id: str,
    order_id: str,
):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:

                cur.execute(
                """
                SELECT
                    id,
                    customer_id,
                    order_id,
                    reason,
                    status,
                    created_at
                FROM refund_requests
                WHERE customer_id = %s
                AND order_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (
                    customer_id,
                    order_id,
                ),
            )

                row = cur.fetchone()

                if row is None:
                    return None

                return {
                "id": str(row[0]),
                "customer_id": row[1],
                "order_id": row[2],
                "reason": row[3],
                "status": row[4],
                "created_at": row[5],
            }


if __name__ == "__main__":

    repo = RefundRepository()

    result = repo.create_refund_request(
        customer_id="customer-002",
        order_id="12345",
        reason="Product is defective",
    )

    print(result)