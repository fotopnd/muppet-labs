"""add synthetic_events_outbox

Revision ID: 002
Revises: 001
Create Date: 2026-06-08

"""

from __future__ import annotations

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE synthetic_events_outbox (
            id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id          UUID        NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
            event_id        UUID        NOT NULL DEFAULT gen_random_uuid(),
            prompt_text     TEXT        NOT NULL,
            response_text   TEXT,
            jailbreak_success  BOOLEAN  NOT NULL,
            classifier_score   FLOAT    NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            published_at    TIMESTAMPTZ
        );
        CREATE INDEX ix_outbox_unpublished ON synthetic_events_outbox (created_at)
            WHERE published_at IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS synthetic_events_outbox;")
