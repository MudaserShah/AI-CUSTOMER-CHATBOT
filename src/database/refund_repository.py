import uuid

from src.database.base_repository import BaseRepository
from src.database.db_utils import handle_db_errors


class RefundRepository(BaseRepository):

    @handle_db_errors
    def get_existing_refund(
        self,
        customer_id: str,
        order_id: str,
    ):
        with self._get_connection() as conn:
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

    @handle_db_errors
    def create_refund_request(
        self,
        customer_id: str,
        order_id: str,
        reason: str,
    ):
        refund_id = uuid.uuid4()

        with self._get_connection() as conn:
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

    @handle_db_errors
    def get_refund_status(
        self,
        customer_id: str,
        order_id: str,
    ):
        with self._get_connection() as conn:
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
