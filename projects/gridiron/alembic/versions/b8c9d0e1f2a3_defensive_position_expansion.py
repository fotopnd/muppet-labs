"""defensive_position_expansion

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-06-23

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "a7b8c9d0e1f2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Split OLB → LOLB (even id) / ROLB (odd id)
    op.execute("UPDATE players SET position='LOLB' WHERE position='OLB' AND id % 2 = 0")
    op.execute("UPDATE players SET position='ROLB' WHERE position='OLB' AND id % 2 = 1")
    # Split S → SS (even id) / FS (odd id)
    op.execute("UPDATE players SET position='SS' WHERE position='S' AND id % 2 = 0")
    op.execute("UPDATE players SET position='FS' WHERE position='S' AND id % 2 = 1")
    # Add s_player_id column to play_log
    op.add_column(
        "play_log",
        sa.Column("s_player_id", sa.Integer(), sa.ForeignKey("players.id"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("play_log", "s_player_id")
    op.execute("UPDATE players SET position='S' WHERE position IN ('SS', 'FS')")
    op.execute("UPDATE players SET position='OLB' WHERE position IN ('LOLB', 'ROLB')")
