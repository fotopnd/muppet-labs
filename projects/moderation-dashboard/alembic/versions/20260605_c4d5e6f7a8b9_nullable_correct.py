"""make classifications.correct nullable for webhook events

Revision ID: c4d5e6f7a8b9
Revises: b3e4f5a6b7c8
Create Date: 2026-06-05 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'b3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('classifications', 'correct', existing_type=sa.Boolean(), nullable=True)


def downgrade() -> None:
    # Set any NULLs to False before re-adding NOT NULL constraint
    op.execute("UPDATE classifications SET correct = false WHERE correct IS NULL")
    op.alter_column('classifications', 'correct', existing_type=sa.Boolean(), nullable=False)
