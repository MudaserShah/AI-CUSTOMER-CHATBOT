"""make customer email unique (case-insensitive)

Revision ID: c8f1a2d3e4b5
Revises: b7e3f6a9c2d1
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c8f1a2d3e4b5"
down_revision: Union[str, Sequence[str], None] = "b7e3f6a9c2d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Run this only after confirming existing customer emails do not contain
    # case-insensitive duplicates. The API relies on one customer per email.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_customers_email_lower
        ON customers (LOWER(email))
        WHERE email IS NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_customers_email_lower;")
