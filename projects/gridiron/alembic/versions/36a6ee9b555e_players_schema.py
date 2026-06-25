"""players_schema

Revision ID: 36a6ee9b555e
Revises: a1b2c3d4e5f6
Create Date: 2026-06-20 22:39:03.951220

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '36a6ee9b555e'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('program_id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.Text(), nullable=False),
        sa.Column('last_name', sa.Text(), nullable=False),
        sa.Column('position', sa.Text(), nullable=False),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('jersey_num', sa.SmallInteger(), nullable=False),
        sa.Column('alpha', sa.Float(), nullable=False),
        sa.Column('delta', sa.Float(), nullable=False),
        sa.Column('sigma', sa.Float(), nullable=False),
        sa.Column('psi', sa.Float(), nullable=False),
        sa.Column('omega', sa.Float(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('alpha BETWEEN 0.0 AND 1.0', name='ck_players_alpha'),
        sa.CheckConstraint('delta BETWEEN 0.0 AND 1.0', name='ck_players_delta'),
        sa.CheckConstraint('omega BETWEEN 0.0 AND 1.0', name='ck_players_omega'),
        sa.CheckConstraint('psi BETWEEN 0.0 AND 1.0', name='ck_players_psi'),
        sa.CheckConstraint('sigma BETWEEN 0.0 AND 1.0', name='ck_players_sigma'),
        sa.CheckConstraint('year BETWEEN 1 AND 4', name='ck_players_year'),
        sa.ForeignKeyConstraint(['program_id'], ['programs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('program_id', 'jersey_num', name='uq_players_program_jersey'),
    )


def downgrade() -> None:
    op.drop_table('players')
