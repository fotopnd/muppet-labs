"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""

from collections.abc import Sequence

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE papers (
            id          SERIAL PRIMARY KEY,
            arxiv_id    VARCHAR(20)  NOT NULL,
            title       TEXT         NOT NULL,
            abstract    TEXT         NOT NULL,
            categories  VARCHAR(200) NOT NULL,
            fetched_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_papers_arxiv_id UNIQUE (arxiv_id)
        )
    """)
    op.execute("CREATE INDEX ix_papers_arxiv_id ON papers (arxiv_id)")

    op.execute("""
        CREATE TABLE experiments (
            id          SERIAL PRIMARY KEY,
            name        VARCHAR(200) NOT NULL,
            description TEXT         NOT NULL DEFAULT '',
            created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_experiments_name UNIQUE (name)
        )
    """)

    op.execute("""
        CREATE TABLE experiment_papers (
            id            SERIAL PRIMARY KEY,
            experiment_id INTEGER     NOT NULL REFERENCES experiments(id),
            paper_id      INTEGER     NOT NULL REFERENCES papers(id),
            condition     VARCHAR(20) NOT NULL,
            CONSTRAINT uq_experiment_papers UNIQUE (experiment_id, paper_id)
        )
    """)
    op.execute(
        "CREATE INDEX ix_experiment_papers_experiment_id ON experiment_papers (experiment_id)"
    )

    op.execute("""
        CREATE TABLE planted_errors (
            id               SERIAL PRIMARY KEY,
            paper_id         INTEGER      NOT NULL REFERENCES papers(id),
            experiment_id    INTEGER      NOT NULL REFERENCES experiments(id),
            category         VARCHAR(30)  NOT NULL,
            original_text    TEXT         NOT NULL,
            altered_text     TEXT         NOT NULL,
            altered_abstract TEXT         NOT NULL,
            rationale        TEXT         NOT NULL,
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_planted_errors UNIQUE (paper_id, experiment_id)
        )
    """)
    op.execute("CREATE INDEX ix_planted_errors_experiment_id ON planted_errors (experiment_id)")

    op.execute("""
        CREATE TABLE review_sessions (
            id            SERIAL PRIMARY KEY,
            experiment_id INTEGER     NOT NULL REFERENCES experiments(id),
            paper_id      INTEGER     NOT NULL REFERENCES papers(id),
            condition     VARCHAR(20) NOT NULL,
            status        VARCHAR(20) NOT NULL DEFAULT 'open',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at  TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ix_review_sessions_experiment_id ON review_sessions (experiment_id)")
    op.execute("CREATE INDEX ix_review_sessions_paper_id ON review_sessions (paper_id)")

    op.execute("""
        CREATE TABLE agent_annotations (
            id                SERIAL PRIMARY KEY,
            review_session_id INTEGER     NOT NULL REFERENCES review_sessions(id),
            text_excerpt      TEXT        NOT NULL,
            confidence        VARCHAR(10) NOT NULL,
            reason            TEXT        NOT NULL,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX ix_agent_annotations_session_id ON agent_annotations (review_session_id)"
    )

    op.execute("""
        CREATE TABLE human_detections (
            id                SERIAL PRIMARY KEY,
            review_session_id INTEGER NOT NULL REFERENCES review_sessions(id),
            text_excerpt      TEXT    NOT NULL,
            note              TEXT,
            is_true_positive  BOOLEAN,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute(
        "CREATE INDEX ix_human_detections_session_id ON human_detections (review_session_id)"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS human_detections")
    op.execute("DROP TABLE IF EXISTS agent_annotations")
    op.execute("DROP TABLE IF EXISTS review_sessions")
    op.execute("DROP TABLE IF EXISTS planted_errors")
    op.execute("DROP TABLE IF EXISTS experiment_papers")
    op.execute("DROP TABLE IF EXISTS experiments")
    op.execute("DROP TABLE IF EXISTS papers")
