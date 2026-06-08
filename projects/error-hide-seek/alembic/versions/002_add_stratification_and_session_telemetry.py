"""add stratification and session telemetry

Revision ID: 002
Revises: 001
Create Date: 2026-06-08

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # experiment_papers: store the category assigned at experiment creation so
    # plant-errors reads from here rather than cycling independently.
    op.execute("""
        ALTER TABLE experiment_papers
            ADD COLUMN intended_category VARCHAR(30)
    """)

    # review_sessions: track blue-team agent run outcome and parse failure count
    # for observability across conditions.
    op.execute("""
        ALTER TABLE review_sessions
            ADD COLUMN agent_run_status VARCHAR(20),
            ADD COLUMN parse_failures    INTEGER NOT NULL DEFAULT 0
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE experiment_papers DROP COLUMN IF EXISTS intended_category")
    op.execute("ALTER TABLE review_sessions DROP COLUMN IF EXISTS agent_run_status")
    op.execute("ALTER TABLE review_sessions DROP COLUMN IF EXISTS parse_failures")
