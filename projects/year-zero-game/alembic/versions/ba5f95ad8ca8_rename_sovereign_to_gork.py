"""rename sovereign to gork

Revision ID: ba5f95ad8ca8
Revises: df9dd4bd52e1
Create Date: 2026-06-16 13:04:53.959175

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba5f95ad8ca8'
down_revision: Union[str, None] = 'df9dd4bd52e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('document_library', 'sovereign_verdict', new_column_name='gork_verdict')
    op.alter_column('document_library', 'sovereign_confidence', new_column_name='gork_confidence')
    op.alter_column('document_library', 'sovereign_reasoning', new_column_name='gork_reasoning')


def downgrade() -> None:
    op.alter_column('document_library', 'gork_verdict', new_column_name='sovereign_verdict')
    op.alter_column('document_library', 'gork_confidence', new_column_name='sovereign_confidence')
    op.alter_column('document_library', 'gork_reasoning', new_column_name='sovereign_reasoning')
