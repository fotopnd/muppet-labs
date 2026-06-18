"""prompt_response_split_resource_model

Revision ID: f3a1c9d7e825
Revises: 4e871a01ad40
Create Date: 2026-06-18 14:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a1c9d7e825"
down_revision: str | None = "4e871a01ad40"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Rename document_text → response_text
    op.alter_column("document_library", "document_text", new_column_name="response_text")

    # Update player verdict constraint: CLEAR/REDACT → ACCEPT/REJECT
    op.drop_constraint("ck_player_verdict", "player_decisions", type_="check")
    op.create_check_constraint(
        "ck_player_verdict",
        "player_decisions",
        "player_verdict IN ('ACCEPT', 'REJECT', 'ESCALATE')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_player_verdict", "player_decisions", type_="check")
    op.create_check_constraint(
        "ck_player_verdict",
        "player_decisions",
        "player_verdict IN ('CLEAR', 'REDACT', 'ESCALATE')",
    )
    op.alter_column("document_library", "response_text", new_column_name="document_text")
