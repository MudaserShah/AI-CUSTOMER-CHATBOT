"""add ecommerce order fields

Revision ID: b7e3f6a9c2d1
Revises: a64e2b1f1cb3
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7e3f6a9c2d1"
down_revision: Union[str, Sequence[str], None] = "a64e2b1f1cb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column(
            "items",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "orders",
        sa.Column("total_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("currency", sa.String(length=3), server_default="USD", nullable=False),
    )
    op.add_column(
        "orders",
        sa.Column("payment_method", sa.String(length=32), server_default="cod", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("orders", "payment_method")
    op.drop_column("orders", "currency")
    op.drop_column("orders", "total_amount")
    op.drop_column("orders", "items")
    op.drop_column("orders", "created_at")
