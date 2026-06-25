"""play_log_down_distance

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-21

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('play_log', sa.Column('down', sa.SmallInteger(), nullable=True))
    op.add_column('play_log', sa.Column('distance', sa.SmallInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column('play_log', 'distance')
    op.drop_column('play_log', 'down')
