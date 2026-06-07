"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-07

"""

from __future__ import annotations

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE attacks (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source        VARCHAR(50)  NOT NULL,
            source_id     VARCHAR(200) NOT NULL,
            harm_category VARCHAR(100) NOT NULL,
            strategy      VARCHAR(100) NOT NULL,
            attack_text   TEXT         NOT NULL,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_attacks_source_source_id ON attacks (source, source_id);
        CREATE INDEX ix_attacks_harm_category ON attacks (harm_category);
        CREATE INDEX ix_attacks_strategy ON attacks (strategy);

        CREATE TABLE run_sessions (
            id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            model_name       VARCHAR(200) NOT NULL,
            total_attacks    INTEGER      NOT NULL DEFAULT 0,
            total_successes  INTEGER      NOT NULL DEFAULT 0,
            asr              FLOAT        NOT NULL DEFAULT 0.0,
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_run_sessions_model_name ON run_sessions (model_name);
        CREATE INDEX ix_run_sessions_created_at ON run_sessions (created_at);

        CREATE TABLE runs (
            id                UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id        UUID    NOT NULL REFERENCES run_sessions(id),
            attack_id         UUID    NOT NULL REFERENCES attacks(id),
            model_name        VARCHAR(200) NOT NULL,
            response_text     TEXT    NOT NULL,
            jailbreak_success BOOLEAN NOT NULL,
            classifier_score  FLOAT   NOT NULL,
            latency_ms        INTEGER NOT NULL,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_runs_session_id ON runs (session_id);
        CREATE INDEX ix_runs_attack_id  ON runs (attack_id);
        CREATE INDEX ix_runs_jailbreak_success ON runs (jailbreak_success);

        CREATE MATERIALIZED VIEW coverage_summary AS
        SELECT
            a.harm_category,
            a.strategy,
            COUNT(*)                                              AS total_runs,
            SUM(CASE WHEN r.jailbreak_success THEN 1 ELSE 0 END) AS total_successes,
            AVG(r.jailbreak_success::int)::float                 AS asr
        FROM runs r
        JOIN attacks a ON r.attack_id = a.id
        GROUP BY a.harm_category, a.strategy;

        CREATE UNIQUE INDEX uix_coverage_summary_category_strategy
            ON coverage_summary (harm_category, strategy);

        CREATE TABLE failure_clusters (
            id         UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
            cluster_id INTEGER NOT NULL,
            run_id     UUID    NOT NULL REFERENCES runs(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX ix_failure_clusters_cluster_id ON failure_clusters (cluster_id);
        CREATE INDEX ix_failure_clusters_run_id     ON failure_clusters (run_id);

        CREATE TABLE cluster_summaries (
            id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            cluster_id        INTEGER      NOT NULL,
            size              INTEGER      NOT NULL,
            top_harm_category VARCHAR(100) NOT NULL,
            top_strategy      VARCHAR(100) NOT NULL,
            representative_text TEXT       NOT NULL,
            computed_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX uix_cluster_summaries_cluster_id ON cluster_summaries (cluster_id);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS cluster_summaries;
        DROP TABLE IF EXISTS failure_clusters;
        DROP MATERIALIZED VIEW IF EXISTS coverage_summary;
        DROP TABLE IF EXISTS runs;
        DROP TABLE IF EXISTS run_sessions;
        DROP TABLE IF EXISTS attacks;
    """)
