"""create projects table and associate conversations with project

Revision ID: d9a2b3c4d5e6
Revises: c8f1a2d3e4b5
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "d9a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c8f1a2d3e4b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("api_key", sa.String(128), nullable=False, unique=True),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("llm_model", sa.String(128), nullable=True),
        sa.Column("widget_title", sa.String(255), server_default="AI Support Assistant", nullable=False),
        sa.Column("widget_greeting", sa.Text(), server_default="Hello! How can I help you today?", nullable=False),
        sa.Column("primary_color", sa.String(32), server_default="#2563eb", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_projects_slug", "projects", ["slug"])
    op.create_index("ix_projects_api_key", "projects", ["api_key"])

    # 2. Seed default TechNest project for backward compatibility
    op.execute(
        """
        INSERT INTO projects (
            id, name, slug, api_key, system_prompt, widget_title, widget_greeting, primary_color
        ) VALUES (
            'technest-default',
            'TechNest Electronics',
            'technest',
            'pk_live_technest_default',
            NULL,
            'TechNest Assistant',
            'Hello! How can I help you with your TechNest orders or inquiries today?',
            '#2563eb'
        ) ON CONFLICT (id) DO NOTHING;
        """
    )

    # 3. Add project_id column to conversations
    op.add_column(
        "conversations",
        sa.Column("project_id", sa.String(64), sa.ForeignKey("projects.id"), server_default="technest-default", nullable=False),
    )
    op.create_index("ix_conversations_project_id", "conversations", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_conversations_project_id", table_name="conversations")
    op.drop_column("conversations", "project_id")
    op.drop_index("ix_projects_api_key", table_name="projects")
    op.drop_index("ix_projects_slug", table_name="projects")
    op.drop_table("projects")
