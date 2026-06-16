"""add is_calibration and needs_review to document_library

Revision ID: 4e871a01ad40
Revises: e7c9f778b014
Create Date: 2026-06-16 20:48:48.038906

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e871a01ad40'
down_revision: Union[str, None] = 'e7c9f778b014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document_library', sa.Column('is_calibration', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('document_library', sa.Column('needs_review', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('ix_document_library_is_calibration', 'document_library', ['is_calibration'])
    op.create_index('ix_document_library_needs_review', 'document_library', ['needs_review'])


def downgrade() -> None:
    op.drop_index('ix_document_library_needs_review', table_name='document_library')
    op.drop_index('ix_document_library_is_calibration', table_name='document_library')
    op.drop_column('document_library', 'needs_review')
    op.drop_column('document_library', 'is_calibration')
