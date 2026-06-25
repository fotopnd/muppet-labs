"""coach_attributes

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-06-25

"""
from __future__ import annotations
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('coaches', sa.Column('run_tendency', sa.Float(), nullable=True))
    op.add_column('coaches', sa.Column('style', sa.Text(), nullable=True))
    op.add_column('coaches', sa.Column('prestige', sa.SmallInteger(), nullable=True))

    op.execute("""
        UPDATE coaches SET run_tendency = ROUND((0.30 + (id % 41) * 0.01)::numeric, 2)
    """)
    op.execute("""
        UPDATE coaches SET style = sub.style
        FROM (
            SELECT id,
                CASE
                    WHEN role = 'Offensive Coordinator' THEN
                        CASE ((ROW_NUMBER() OVER (PARTITION BY role ORDER BY id) - 1) % 5)
                            WHEN 0 THEN 'balanced'
                            WHEN 1 THEN 'spread'
                            WHEN 2 THEN 'power_run'
                            WHEN 3 THEN 'west_coast'
                            WHEN 4 THEN 'air_raid'
                        END
                    WHEN role = 'Defensive Coordinator' THEN
                        CASE ((ROW_NUMBER() OVER (PARTITION BY role ORDER BY id) - 1) % 4)
                            WHEN 0 THEN '4-3'
                            WHEN 1 THEN '3-4'
                            WHEN 2 THEN 'nickel'
                            WHEN 3 THEN 'blitz_heavy'
                        END
                    ELSE 'balanced'
                END AS style
            FROM coaches
        ) sub
        WHERE coaches.id = sub.id
    """)
    op.execute("""
        UPDATE coaches SET prestige = GREATEST(1, CEIL(rating * 5))::smallint
    """)

    op.alter_column('coaches', 'run_tendency', nullable=False)
    op.alter_column('coaches', 'style', nullable=False)
    op.alter_column('coaches', 'prestige', nullable=False)
    op.create_check_constraint('ck_coaches_prestige', 'coaches', 'prestige BETWEEN 1 AND 5')


def downgrade() -> None:
    op.drop_constraint('ck_coaches_prestige', 'coaches', type_='check')
    op.drop_column('coaches', 'prestige')
    op.drop_column('coaches', 'style')
    op.drop_column('coaches', 'run_tendency')
