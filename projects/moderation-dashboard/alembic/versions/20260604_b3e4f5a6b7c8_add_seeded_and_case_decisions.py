"""add seeded column and case_decisions table

Revision ID: b3e4f5a6b7c8
Revises: ea2e59677dbb
Create Date: 2026-06-04 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b3e4f5a6b7c8'
down_revision: Union[str, None] = 'ea2e59677dbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'classifications',
        sa.Column('seeded', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.create_table(
        'case_decisions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('escalation_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('escalation_id'),
    )
    op.create_index('ix_case_decisions_escalation_id', 'case_decisions', ['escalation_id'])


def downgrade() -> None:
    op.drop_index('ix_case_decisions_escalation_id', table_name='case_decisions')
    op.drop_table('case_decisions')
    op.drop_column('classifications', 'seeded')
