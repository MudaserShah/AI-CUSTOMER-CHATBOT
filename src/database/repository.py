import os
import psycopg
from dotenv import load_dotenv
import uuid

load_dotenv()

POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://ai_chatbot:Shahg@401@localhost:5432/ai_customer_chatbot")

class CustomerRepository:

    def __init__(self, connection_uri: str = POSTGRES_URI):
        self.database_url = connection_uri

    def create_customer(self, customer_id, name, email):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO customers (customer_id, name, email)
                    VALUES (%s, %s, %s)
                    RETURNING id, customer_id, name, email, created_at;
                    """,
                    (customer_id, name, email)
                )

                return cur.fetchone()

    def get_customer(self, customer_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
    """
    SELECT id, customer_id, name, email, created_at
    FROM customers
    WHERE customer_id = %s;
    """,
    (customer_id,)
)
                return cur.fetchone()
    def create_conversation(self, customer_id, thread_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
    """
    INSERT INTO conversations (customer_id, thread_id)
    VALUES (%s, %s)
    RETURNING id, customer_id, thread_id, created_at;
    """,
    (customer_id, thread_id)
)
                return cur.fetchone()

    def get_customer_email(self, customer_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                """
                SELECT email
                FROM customers
                WHERE customer_id = %s;
                """,
                (customer_id,)
            )

                row = cur.fetchone()

                if row is None:
                    return None

                return row[0]
            
    def get_conversation(self, customer_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
            """
            SELECT id, customer_id, thread_id, created_at
            FROM conversations
            WHERE customer_id = %s
            ORDER BY created_at DESC
            LIMIT 1;
            """,
            (customer_id,)
        )

                return cur.fetchone()

    def get_or_create_customer(self, customer_id, name=None, email=None):
        customer = self.get_customer(customer_id)
        if customer:
            return customer
        return self.create_customer(
             customer_id,
             name,
             email
        )

    def get_or_create_conversation(self, customer_id):
        conversation = self.get_conversation(customer_id)
        if conversation:
            return conversation
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"
        return self.create_conversation(
    customer_id,
    thread_id
)
    def get_conversations(self, customer_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                """
                SELECT id, customer_id, thread_id, created_at
                FROM conversations
                WHERE customer_id = %s
                ORDER BY created_at DESC;
                """,
                (customer_id,)
            )

                return cur.fetchall()
    def create_new_conversation(self, customer_id):
        thread_id = f"thread_{uuid.uuid4().hex[:12]}"

        return self.create_conversation(
        customer_id,
        thread_id
    )


if __name__ == "__main__":
    
    repo = CustomerRepository()

    conversation = repo.create_new_conversation("customer-002")

    print(conversation)