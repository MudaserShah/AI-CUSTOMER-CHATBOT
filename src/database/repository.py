import uuid

from src.database.base_repository import BaseRepository
from src.database.db_utils import handle_db_errors


class CustomerRepository(BaseRepository):
    @handle_db_errors
    def create_customer(self, customer_id, name, email):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO customers (customer_id, name, email)
                    VALUES (%s, %s, %s)
                    RETURNING id, customer_id, name, email, created_at;
                    """,
                    (customer_id, name, email),
                )
                return cur.fetchone()

    @handle_db_errors
    def get_customer(self, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, customer_id, name, email, created_at
                    FROM customers
                    WHERE customer_id = %s;
                    """,
                    (customer_id,),
                )
                return cur.fetchone()

    @handle_db_errors
    def get_customer_by_email(self, email):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, customer_id, name, email, created_at
                    FROM customers
                    WHERE LOWER(email) = LOWER(%s)
                    ORDER BY created_at ASC
                    LIMIT 1;
                    """,
                    (email,),
                )
                return cur.fetchone()

    @handle_db_errors
    def create_conversation(self, customer_id, thread_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversations (customer_id, thread_id)
                    VALUES (%s, %s)
                    RETURNING id, customer_id, thread_id, created_at;
                    """,
                    (customer_id, thread_id),
                )
                return cur.fetchone()

    @handle_db_errors
    def get_customer_email(self, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT email
                    FROM customers
                    WHERE customer_id = %s;
                    """,
                    (customer_id,),
                )
                row = cur.fetchone()
                return None if row is None else row[0]

    @handle_db_errors
    def get_conversation(self, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, customer_id, thread_id, created_at
                    FROM conversations
                    WHERE customer_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1;
                    """,
                    (customer_id,),
                )
                return cur.fetchone()

    def get_or_create_customer(self, customer_id, name=None, email=None):
        customer = self.get_customer(customer_id)
        if customer:
            return customer
        return self.create_customer(customer_id, name, email)

    def get_or_create_conversation(self, customer_id):
        conversation = self.get_conversation(customer_id)
        if conversation:
            return conversation
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        return self.create_conversation(customer_id, thread_id)

    @handle_db_errors
    def get_conversations(self, customer_id):
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, customer_id, thread_id, created_at
                    FROM conversations
                    WHERE customer_id = %s
                    ORDER BY created_at DESC;
                    """,
                    (customer_id,),
                )
                return cur.fetchall()

    def create_new_conversation(self, customer_id):
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        return self.create_conversation(customer_id, thread_id)
