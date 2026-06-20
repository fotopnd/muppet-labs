"""conglomerate_region_colors

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-20

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('conglomerates', sa.Column('region', sa.Text(), nullable=False, server_default=''))
    op.add_column('conglomerates', sa.Column('primary_color', sa.CHAR(length=7), nullable=False, server_default='#000000'))
    op.add_column('conglomerates', sa.Column('secondary_color', sa.CHAR(length=7), nullable=False, server_default='#000000'))
    op.add_column('conglomerates', sa.Column('tertiary_color', sa.CHAR(length=7), nullable=False, server_default='#000000'))
    op.alter_column('conglomerates', 'region', server_default=None)
    op.alter_column('conglomerates', 'primary_color', server_default=None)
    op.alter_column('conglomerates', 'secondary_color', server_default=None)
    op.alter_column('conglomerates', 'tertiary_color', server_default=None)


def downgrade() -> None:
    op.drop_column('conglomerates', 'tertiary_color')
    op.drop_column('conglomerates', 'secondary_color')
    op.drop_column('conglomerates', 'primary_color')
    op.drop_column('conglomerates', 'region')
