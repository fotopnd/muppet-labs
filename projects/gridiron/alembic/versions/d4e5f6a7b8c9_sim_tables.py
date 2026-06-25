"""sim_tables

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-21

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # programs: add current elo column, initialised from seed midpoint
    op.add_column('programs', sa.Column('elo', sa.Float(), nullable=False, server_default='1500.0'))
    op.execute('UPDATE programs SET elo = (elo_seed_min + elo_seed_max) / 2.0')
    op.alter_column('programs', 'elo', server_default=None)

    # games: add sim columns
    for col, typ, default in [
        ('broadcast_slot', sa.Text(), 'noon'),
        ('is_postseason',  sa.Boolean(), 'false'),
        ('elo_tiebreak',   sa.Boolean(), 'false'),
    ]:
        op.add_column('games', sa.Column(col, typ, nullable=False, server_default=default))
        op.alter_column('games', col, server_default=None)

    for col in ('home_elo_pre', 'away_elo_pre', 'home_elo_post', 'away_elo_post'):
        op.add_column('games', sa.Column(col, sa.Float(), nullable=True))

    # play_log
    op.create_table(
        'play_log',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.id'), nullable=False),
        sa.Column('play_number', sa.SmallInteger(), nullable=False),
        sa.Column('quarter', sa.SmallInteger(), nullable=False),
        sa.Column('possession', sa.CHAR(4), nullable=False),
        sa.Column('play_type', sa.Text(), nullable=False),
        sa.Column('yards_gained', sa.SmallInteger(), nullable=True),
        sa.Column('field_pos_before', sa.SmallInteger(), nullable=False),
        sa.Column('field_pos_after', sa.SmallInteger(), nullable=True),
        sa.Column('score_home', sa.SmallInteger(), nullable=False),
        sa.Column('score_away', sa.SmallInteger(), nullable=False),
        sa.Column('primary_player_id', sa.Integer(), sa.ForeignKey('players.id'), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('x_coord', sa.SmallInteger(), nullable=True),
        sa.Column('y_coord', sa.SmallInteger(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
    )
    op.create_index('play_log_game_idx', 'play_log', ['game_id', 'play_number'])

    # player_game_stats
    stat_cols = [
        ('pass_attempts', 0), ('pass_completions', 0), ('pass_yards', 0),
        ('pass_tds', 0), ('interceptions', 0),
        ('rush_attempts', 0), ('rush_yards', 0), ('rush_tds', 0),
        ('targets', 0), ('receptions', 0), ('receiving_yards', 0), ('receiving_tds', 0),
        ('tackles', 0), ('sacks', 0), ('forced_fumbles', 0), ('ints_def', 0),
        ('fg_attempts', 0), ('fg_made', 0),
    ]
    op.create_table(
        'player_game_stats',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('game_id', sa.Integer(), sa.ForeignKey('games.id'), nullable=False),
        sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.id'), nullable=False),
        sa.Column('program_id', sa.Integer(), sa.ForeignKey('programs.id'), nullable=False),
        *[sa.Column(n, sa.SmallInteger(), server_default=str(d), nullable=False) for n, d in stat_cols],
        sa.UniqueConstraint('game_id', 'player_id', name='uq_player_game_stats'),
    )


def downgrade() -> None:
    op.drop_table('player_game_stats')
    op.drop_index('play_log_game_idx', table_name='play_log')
    op.drop_table('play_log')
    for col in ('elo_tiebreak', 'home_elo_post', 'away_elo_post', 'home_elo_pre',
                'away_elo_pre', 'is_postseason', 'broadcast_slot'):
        op.drop_column('games', col)
    op.drop_column('programs', 'elo')
