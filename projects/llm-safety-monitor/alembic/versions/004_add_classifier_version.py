"""Add classifier_version to classifications and enforce idempotent uniqueness

Revision ID: 004
Revises: 003
Create Date: 2026-06-08
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: add nullable column so existing rows don't violate NOT NULL yet
    op.add_column(
        "classifications",
        sa.Column("classifier_version", sa.String(100), nullable=True),
    )

    # Step 2: backfill — all pre-versioning rows become 'legacy'
    op.execute("UPDATE classifications SET classifier_version = 'legacy' WHERE classifier_version IS NULL")

    # Step 3: deduplicate non-null event_id rows (keep latest by processed_at per event/model)
    # Null event_id rows (legacy/seeded) are left untouched — they won't conflict because
    # PostgreSQL treats NULLs as distinct in UNIQUE constraints.
    op.execute("""
        DELETE FROM classifications
        WHERE event_id IS NOT NULL
          AND id NOT IN (
            SELECT DISTINCT ON (event_id, model_name) id
            FROM classifications
            WHERE event_id IS NOT NULL
            ORDER BY event_id, model_name, processed_at DESC NULLS LAST
          )
    """)

    # Step 4: make NOT NULL now that all rows have a value
    op.alter_column("classifications", "classifier_version", nullable=False)

    # Step 5: unique constraint — allows re-evaluation with a new classifier version
    # without conflicting with existing results
    op.create_unique_constraint(
        "uq_classifications_event_model_version",
        "classifications",
        ["event_id", "model_name", "classifier_version"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_classifications_event_model_version", "classifications")
    op.drop_column("classifications", "classifier_version")
