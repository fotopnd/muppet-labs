"""Add human_decision column to interactions

Revision ID: 003
Revises: 002
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "interactions",
        sa.Column("human_decision", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interactions", "human_decision")
