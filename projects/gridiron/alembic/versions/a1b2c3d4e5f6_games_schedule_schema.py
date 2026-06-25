"""games_schedule_schema

Revision ID: a1b2c3d4e5f6
Revises: 33f31770f03e
Create Date: 2026-06-20 19:28:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '33f31770f03e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rivalry_pairs',
        sa.Column('program_a_id', sa.Integer(), nullable=False),
        sa.Column('program_b_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['program_a_id'], ['programs.id']),
        sa.ForeignKeyConstraint(['program_b_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('program_a_id', 'program_b_id'),
        sa.CheckConstraint('program_a_id < program_b_id', name='ck_rivalry_pairs_order'),
    )

    op.create_table(
        'games',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('season', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('week', sa.SmallInteger(), nullable=False),
        sa.Column('home_program_id', sa.Integer(), nullable=True),
        sa.Column('away_program_id', sa.Integer(), nullable=True),
        sa.Column('is_rivalry', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('status', sa.Text(), nullable=False, server_default='scheduled'),
        sa.Column('home_score', sa.SmallInteger(), nullable=True),
        sa.Column('away_score', sa.SmallInteger(), nullable=True),
        sa.Column('scheduled_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('ended_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['home_program_id'], ['programs.id']),
        sa.ForeignKeyConstraint(['away_program_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('week BETWEEN 1 AND 26', name='ck_games_week_range'),
        sa.CheckConstraint('home_program_id != away_program_id', name='ck_games_no_self_play'),
    )


def downgrade() -> None:
    op.drop_table('games')
    op.drop_table('rivalry_pairs')
