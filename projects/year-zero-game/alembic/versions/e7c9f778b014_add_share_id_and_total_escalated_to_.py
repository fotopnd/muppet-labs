"""add share_id and total_escalated to game_sessions

Revision ID: e7c9f778b014
Revises: ba5f95ad8ca8
Create Date: 2026-06-16 13:30:20.539767

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7c9f778b014'
down_revision: Union[str, None] = 'ba5f95ad8ca8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('game_sessions', sa.Column('share_id', sa.String(12), nullable=True))
    op.create_unique_constraint('uq_game_sessions_share_id', 'game_sessions', ['share_id'])
    op.create_index('ix_game_sessions_share_id', 'game_sessions', ['share_id'])
    op.add_column('game_sessions', sa.Column('total_escalated', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_index('ix_game_sessions_share_id', table_name='game_sessions')
    op.drop_constraint('uq_game_sessions_share_id', 'game_sessions', type_='unique')
    op.drop_column('game_sessions', 'share_id')
    op.drop_column('game_sessions', 'total_escalated')
