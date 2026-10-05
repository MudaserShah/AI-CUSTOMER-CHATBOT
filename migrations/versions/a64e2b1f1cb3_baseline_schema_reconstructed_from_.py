r"""baseline schema reconstructed from existing ad hoc tables

Revision ID: a64e2b1f1cb3
Revises:
Create Date: 2026-10-03 10:07:25.005135

IMPORTANT — read before running this:

This project's tables (customers, conversations, orders,
refund_requests) were originally created by hand, with no migration
tool and no schema file (see the production-readiness report, finding
F4). This migration reconstructs that schema from the columns used
throughout src/database/*.py, so that from this point forward, every
future schema change is tracked by a migration instead of a manual
`CREATE TABLE`/`ALTER TABLE` someone has to remember they ran.

Because it's a reconstruction, not a dump of the real schema, verify
it against your actual database before trusting it — for example:

    psql "$POSTGRES_URI" -c "\d customers"
    psql "$POSTGRES_URI" -c "\d conversations"
    psql "$POSTGRES_URI" -c "\d orders"
    psql "$POSTGRES_URI" -c "\d refund_requests"

...and adjust the column types/constraints below (nullability, string
lengths, defaults) to match what you actually have. The column *names*
are correct (every one is used in a live query somewhere in the
codebase); the exact types are a best-effort guess.

Two different ways to apply this, depending on the database:

  * Your EXISTING database (tables already exist):
    Do NOT run `alembic upgrade head` — that would try to CREATE TABLE
    on tables that are already there and fail. Instead, tell Alembic
    "the database is already at this point":

        alembic stamp head

  * A FRESH database (a new teammate's machine, CI, staging):
    Tables don't exist yet, so the normal command creates them:

        alembic upgrade head
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a64e2b1f1cb3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String, nullable=False, unique=True),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("email", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.String, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("thread_id", sa.String, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])

    op.create_table(
        "orders",
        sa.Column("order_id", sa.String, primary_key=True),
        sa.Column("customer_id", sa.String, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("dispatch_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shipping_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("receiving_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_address", sa.String, nullable=True),
    )
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])

    op.create_table(
        "refund_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("customer_id", sa.String, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("order_id", sa.String, sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("reason", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refund_requests_customer_id", "refund_requests", ["customer_id"])
    op.create_index("ix_refund_requests_order_id", "refund_requests", ["order_id"])

    # src/services/refund_service.py explicitly catches UniqueViolation
    # as an expected race-condition outcome when two requests try to
    # create a refund for the same order at once — that only works if
    # the database actually enforces uniqueness. A plain UNIQUE
    # constraint would block ever re-requesting a refund after it's
    # rejected/completed, so this is a PARTIAL unique index: only one
    # pending/approved refund request can exist per (customer, order)
    # at a time, matching the check in create_refund_request().
    # VERIFY this matches your real database — if your live DB has a
    # different constraint (or none at all), the race-condition
    # handling in refund_service.py silently does nothing.
    op.create_index(
        "uq_refund_requests_active_per_order",
        "refund_requests",
        ["customer_id", "order_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'approved')"),
    )


def downgrade() -> None:
    op.drop_table("refund_requests")
    op.drop_table("orders")
    op.drop_table("conversations")
    op.drop_table("customers")
