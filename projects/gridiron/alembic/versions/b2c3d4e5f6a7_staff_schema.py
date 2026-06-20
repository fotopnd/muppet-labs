"""staff_schema

Revision ID: b2c3d4e5f6a7
Revises: 36a6ee9b555e
Create Date: 2026-06-20 17:10:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = '36a6ee9b555e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'coaches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.Text(), nullable=False),
        sa.Column('first_name', sa.Text(), nullable=False),
        sa.Column('last_name', sa.Text(), nullable=False),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating BETWEEN 0.0 AND 1.0', name='ck_coaches_rating'),
    )
    op.create_index('ix_coaches_program_id', 'coaches', ['program_id'])

    op.create_table(
        'boosters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.Text(), nullable=False),
        sa.Column('last_name', sa.Text(), nullable=False),
        sa.Column('influence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('influence BETWEEN 0.0 AND 1.0', name='ck_boosters_influence'),
    )
    op.create_index('ix_boosters_program_id', 'boosters', ['program_id'])


def downgrade() -> None:
    op.drop_index('ix_boosters_program_id', table_name='boosters')
    op.drop_table('boosters')
    op.drop_index('ix_coaches_program_id', table_name='coaches')
    op.drop_table('coaches')
