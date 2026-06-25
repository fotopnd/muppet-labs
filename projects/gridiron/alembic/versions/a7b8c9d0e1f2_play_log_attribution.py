"""play_log_attribution

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-23

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for col in [
        "secondary_player_id",
        "tackler_player_id",
        "ol_player_id",
        "dl_player_id",
        "lb_player_id",
    ]:
        op.add_column(
            "play_log",
            sa.Column(col, sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
        )


def downgrade() -> None:
    for col in [
        "lb_player_id",
        "dl_player_id",
        "ol_player_id",
        "tackler_player_id",
        "secondary_player_id",
    ]:
        op.drop_column("play_log", col)
