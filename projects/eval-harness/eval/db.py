from __future__ import annotations

import contextlib
import sqlite3
from collections.abc import Generator
from pathlib import Path

from eval.models import DatasetSource, EvalResult, EvalRun, TestCase

SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS eval_runs (
    id           TEXT PRIMARY KEY,
    config_json  TEXT NOT NULL,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    total_cases  INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'running',
    mean_score   REAL,
    refusal_rate REAL,
    run_label    TEXT
);

CREATE TABLE IF NOT EXISTS eval_results (
    id                    TEXT PRIMARY KEY,
    run_id                TEXT NOT NULL REFERENCES eval_runs(id),
    case_id               TEXT NOT NULL,
    prompt                TEXT NOT NULL,
    raw_response          TEXT NOT NULL,
    latency_ms            INTEGER NOT NULL,
    refusal_detected      INTEGER NOT NULL,
    expect_refusal        INTEGER NOT NULL DEFAULT 0,
    criterion_scores_json TEXT NOT NULL,
    aggregate_score       REAL,
    created_at            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS test_cases (
    id                TEXT PRIMARY KEY,
    prompt            TEXT NOT NULL,
    dataset           TEXT NOT NULL,
    tags_json         TEXT NOT NULL DEFAULT '[]',
    reference_answer  TEXT,
    expect_refusal    INTEGER NOT NULL DEFAULT 0,
    rubric_names_json TEXT NOT NULL DEFAULT '[]',
    metadata_json     TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS idx_results_run_id  ON eval_results(run_id);
CREATE INDEX IF NOT EXISTS idx_results_case_id ON eval_results(case_id);
CREATE INDEX IF NOT EXISTS idx_runs_started_at ON eval_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_label      ON eval_runs(run_label);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextlib.contextmanager
def get_db(db_path: Path) -> Generator[sqlite3.Connection, None, None]:
    conn = _connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_db(db_path) as conn:
        conn.executescript(_DDL)
        conn.execute("INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))


def insert_run(conn: sqlite3.Connection, run: EvalRun) -> None:
    conn.execute(
        """INSERT INTO eval_runs (id, config_json, started_at, total_cases, status, run_label)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            run.id,
            run.config.model_dump_json(),
            run.started_at.isoformat(),
            run.total_cases,
            run.status,
            run.config.run_label,
        ),
    )


def update_run(conn: sqlite3.Connection, run: EvalRun) -> None:
    conn.execute(
        """UPDATE eval_runs
           SET finished_at=?, status=?, total_cases=?, mean_score=?, refusal_rate=?
           WHERE id=?""",
        (
            run.finished_at.isoformat() if run.finished_at else None,
            run.status,
            run.total_cases,
            run.mean_score,
            run.refusal_rate,
            run.id,
        ),
    )


def insert_result(conn: sqlite3.Connection, result: EvalResult) -> None:
    import json

    conn.execute(
        """INSERT INTO eval_results
           (id, run_id, case_id, prompt, raw_response, latency_ms,
            refusal_detected, expect_refusal, criterion_scores_json, aggregate_score, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result.id,
            result.run_id,
            result.case_id,
            result.prompt,
            result.raw_response,
            result.latency_ms,
            int(result.refusal_detected),
            int(result.expect_refusal),
            json.dumps([cs.model_dump() for cs in result.criterion_scores]),
            result.aggregate_score,
            result.created_at.isoformat(),
        ),
    )


def get_run(conn: sqlite3.Connection, run_id: str) -> EvalRun | None:
    row = conn.execute("SELECT * FROM eval_runs WHERE id=?", (run_id,)).fetchone()
    if not row:
        return None
    return _row_to_run(row)


def get_run_by_label(conn: sqlite3.Connection, label: str) -> EvalRun | None:
    row = conn.execute(
        "SELECT * FROM eval_runs WHERE run_label LIKE ? ORDER BY started_at DESC LIMIT 1",
        (f"%{label}%",),
    ).fetchone()
    return _row_to_run(row) if row else None


def list_runs(
    conn: sqlite3.Connection,
    limit: int = 20,
    status: str | None = None,
) -> list[EvalRun]:
    if status and status != "all":
        rows = conn.execute(
            "SELECT * FROM eval_runs WHERE status=? ORDER BY started_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM eval_runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_run(r) for r in rows]


def get_results_for_run(conn: sqlite3.Connection, run_id: str) -> list[EvalResult]:
    rows = conn.execute(
        "SELECT * FROM eval_results WHERE run_id=? ORDER BY created_at ASC", (run_id,)
    ).fetchall()
    return [_row_to_result(r) for r in rows]


def get_last_two_completed_runs(conn: sqlite3.Connection) -> tuple[EvalRun, EvalRun] | None:
    rows = conn.execute(
        "SELECT * FROM eval_runs WHERE status='complete' ORDER BY started_at DESC LIMIT 2"
    ).fetchall()
    if len(rows) < 2:
        return None
    # rows[0] is most recent (run_b), rows[1] is second-to-last (run_a)
    return _row_to_run(rows[1]), _row_to_run(rows[0])


def insert_test_case(conn: sqlite3.Connection, case: TestCase) -> None:
    import json

    conn.execute(
        """INSERT INTO test_cases
           (id, prompt, dataset, tags_json, reference_answer,
            expect_refusal, rubric_names_json, metadata_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            case.id,
            case.prompt,
            case.dataset.value,
            json.dumps(case.tags),
            case.reference_answer,
            int(case.expect_refusal),
            json.dumps(case.rubric_names),
            json.dumps(case.metadata),
        ),
    )


def get_test_case(conn: sqlite3.Connection, case_id: str) -> TestCase | None:
    row = conn.execute("SELECT * FROM test_cases WHERE id=?", (case_id,)).fetchone()
    return _row_to_case(row) if row else None


def list_test_cases(
    conn: sqlite3.Connection,
    dataset: DatasetSource | None = None,
) -> list[TestCase]:
    if dataset:
        rows = conn.execute("SELECT * FROM test_cases WHERE dataset=?", (dataset.value,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM test_cases").fetchall()
    return [_row_to_case(r) for r in rows]


# ── Private helpers ────────────────────────────────────────────────────────────


def _row_to_run(row: sqlite3.Row) -> EvalRun:
    from datetime import datetime

    from eval.models import RunConfig

    finished = datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None
    return EvalRun(
        id=row["id"],
        config=RunConfig.model_validate_json(row["config_json"]),
        started_at=datetime.fromisoformat(row["started_at"]),
        finished_at=finished,
        total_cases=row["total_cases"],
        status=row["status"],
        mean_score=row["mean_score"],
        refusal_rate=row["refusal_rate"],
    )


def _row_to_result(row: sqlite3.Row) -> EvalResult:
    import json
    from datetime import datetime

    from eval.models import CriterionScore

    scores = [CriterionScore.model_validate(cs) for cs in json.loads(row["criterion_scores_json"])]
    return EvalResult(
        id=row["id"],
        run_id=row["run_id"],
        case_id=row["case_id"],
        prompt=row["prompt"],
        raw_response=row["raw_response"],
        latency_ms=row["latency_ms"],
        refusal_detected=bool(row["refusal_detected"]),
        expect_refusal=bool(row["expect_refusal"]),
        criterion_scores=scores,
        aggregate_score=row["aggregate_score"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_case(row: sqlite3.Row) -> TestCase:
    import json

    return TestCase(
        id=row["id"],
        prompt=row["prompt"],
        dataset=DatasetSource(row["dataset"]),
        tags=json.loads(row["tags_json"]),
        reference_answer=row["reference_answer"],
        expect_refusal=bool(row["expect_refusal"]),
        rubric_names=json.loads(row["rubric_names_json"]),
        metadata=json.loads(row["metadata_json"]),
    )
