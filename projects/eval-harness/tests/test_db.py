from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import pytest

from eval.db import (
    get_db,
    get_last_two_completed_runs,
    get_results_for_run,
    get_run,
    get_test_case,
    init_db,
    insert_result,
    insert_run,
    insert_test_case,
    list_runs,
    update_run,
)
from eval.models import (
    DatasetSource,
    EvalResult,
    EvalRun,
    ModelBackend,
    RunConfig,
    TestCase,
)


def _make_run(label: str = "test") -> EvalRun:
    return EvalRun(
        config=RunConfig(
            model_backend=ModelBackend.LOCAL,
            model_name="qwen",
            dataset_names=[DatasetSource.CUSTOM],
            rubric_names=[],
            run_label=label,
        )
    )


def _make_result(run_id: str, case_id: str = "custom:x") -> EvalResult:
    return EvalResult(
        run_id=run_id,
        case_id=case_id,
        prompt="test",
        raw_response="response",
        latency_ms=100,
        refusal_detected=False,
        expect_refusal=False,
        criterion_scores=[],
        aggregate_score=0.8,
    )


def test_init_db_idempotent(tmp_db: Path):
    init_db(tmp_db)  # second call should not raise
    init_db(tmp_db)  # third call too


def test_insert_and_get_run(tmp_db: Path):
    run = _make_run()
    with get_db(tmp_db) as conn:
        insert_run(conn, run)
        fetched = get_run(conn, run.id)
    assert fetched is not None
    assert fetched.id == run.id
    assert fetched.config.model_name == "qwen"
    assert fetched.status == "running"


def test_update_run(tmp_db: Path):
    run = _make_run()
    with get_db(tmp_db) as conn:
        insert_run(conn, run)
    run.status = "complete"
    run.finished_at = datetime.now(UTC)
    run.mean_score = 0.75
    run.refusal_rate = 0.9
    run.total_cases = 5
    with get_db(tmp_db) as conn:
        update_run(conn, run)
        fetched = get_run(conn, run.id)
    assert fetched.status == "complete"
    assert fetched.mean_score == 0.75


def test_list_runs(tmp_db: Path):
    with get_db(tmp_db) as conn:
        for i in range(3):
            insert_run(conn, _make_run(f"run-{i}"))
    with get_db(tmp_db) as conn:
        runs = list_runs(conn, limit=10)
    assert len(runs) == 3


def test_insert_and_get_result(tmp_db: Path):
    run = _make_run()
    with get_db(tmp_db) as conn:
        insert_run(conn, run)
    result = _make_result(run.id)
    with get_db(tmp_db) as conn:
        insert_result(conn, result)
        results = get_results_for_run(conn, run.id)
    assert len(results) == 1
    assert results[0].run_id == run.id
    assert results[0].aggregate_score == 0.8
    assert results[0].refusal_detected is False


def test_insert_and_get_test_case(tmp_db: Path):
    case = TestCase(
        id="custom:abc",
        prompt="Test prompt",
        dataset=DatasetSource.CUSTOM,
        tags=["tag1"],
        expect_refusal=True,
        rubric_names=["refusal_detection"],
    )
    with get_db(tmp_db) as conn:
        insert_test_case(conn, case)
        fetched = get_test_case(conn, "custom:abc")
    assert fetched is not None
    assert fetched.expect_refusal is True
    assert fetched.tags == ["tag1"]


def test_insert_duplicate_test_case_raises(tmp_db: Path):
    case = TestCase(id="custom:dup", prompt="p", dataset=DatasetSource.CUSTOM)
    with get_db(tmp_db) as conn:
        insert_test_case(conn, case)
    with pytest.raises(sqlite3.IntegrityError):
        with get_db(tmp_db) as conn:
            insert_test_case(conn, case)


def test_get_last_two_completed_runs(tmp_db: Path):
    runs = [_make_run(f"run-{i}") for i in range(3)]
    with get_db(tmp_db) as conn:
        for run in runs:
            insert_run(conn, run)
    # Complete first two
    for run in runs[:2]:
        run.status = "complete"
        run.finished_at = datetime.now(UTC)
        with get_db(tmp_db) as conn:
            update_run(conn, run)
    with get_db(tmp_db) as conn:
        pair = get_last_two_completed_runs(conn)
    assert pair is not None
    ra, rb = pair
    assert ra.config.run_label in ("run-0", "run-1")
    assert rb.config.run_label in ("run-0", "run-1")
    assert ra.id != rb.id


def test_get_last_two_returns_none_if_fewer(tmp_db: Path):
    run = _make_run()
    run.status = "complete"
    run.finished_at = datetime.now(UTC)
    with get_db(tmp_db) as conn:
        insert_run(conn, run)
        update_run(conn, run)
        result = get_last_two_completed_runs(conn)
    assert result is None
