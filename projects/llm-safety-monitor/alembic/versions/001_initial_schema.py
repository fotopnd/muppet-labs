"""Initial schema: interactions table + classifications table with event_id FK

Revision ID: 001
Revises:
Create Date: 2026-06-06
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("source_dataset", sa.String(50), nullable=False),
        sa.Column("ground_truth_safe", sa.Boolean(), nullable=True),
        sa.Column("ground_truth_categories", JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("escalated", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("escalation_reason", sa.String(50), nullable=True),
    )

    op.create_table(
        "classifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("model_name", sa.String(100), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("predicted_label", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("seeded", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "event_id",
            UUID(as_uuid=True),
            sa.ForeignKey("interactions.id"),
            nullable=True,
        ),
        sa.Column("taxonomy_labels", JSONB(), nullable=True),
    )

    op.create_index("ix_classifications_model_name", "classifications", ["model_name"])
    op.create_index("ix_classifications_event_id", "classifications", ["event_id"])
    op.create_index("ix_classifications_processed_at", "classifications", ["processed_at"])
    op.create_index("ix_interactions_created_at", "interactions", ["created_at"])
    op.create_index("ix_interactions_escalated", "interactions", ["escalated"])


def downgrade() -> None:
    op.drop_table("classifications")
    op.drop_table("interactions")
