from __future__ import annotations

from eval.drift import _direction, compute_drift
from eval.models import (
    DatasetSource,
    EvalResult,
    EvalRun,
    ModelBackend,
    RunConfig,
)


def _run(label: str, mean_score: float | None = None, refusal_rate: float | None = None) -> EvalRun:
    run = EvalRun(
        config=RunConfig(
            model_backend=ModelBackend.LOCAL,
            model_name="qwen",
            dataset_names=[DatasetSource.CUSTOM],
            rubric_names=[],
            run_label=label,
        )
    )
    run.status = "complete"
    run.mean_score = mean_score
    run.refusal_rate = refusal_rate
    return run


def _result(
    run_id: str,
    case_id: str,
    aggregate_score: float | None = 0.8,
    refusal_detected: bool = False,
    expect_refusal: bool = False,
) -> EvalResult:
    return EvalResult(
        run_id=run_id,
        case_id=case_id,
        prompt="p",
        raw_response="r",
        latency_ms=100,
        refusal_detected=refusal_detected,
        expect_refusal=expect_refusal,
        aggregate_score=aggregate_score,
    )


def test_direction():
    assert _direction(0.05) == "up"
    assert _direction(-0.05) == "down"
    assert _direction(0.0) == "unchanged"
    assert _direction(None) == "unknown"


def test_zero_delta():
    ra = _run("a", mean_score=0.7, refusal_rate=0.9)
    rb = _run("b", mean_score=0.7, refusal_rate=0.9)
    results_a = [_result(ra.id, "custom:1"), _result(ra.id, "custom:2")]
    results_b = [_result(rb.id, "custom:1"), _result(rb.id, "custom:2")]
    report = compute_drift(ra, results_a, rb, results_b)
    mean_delta = next(m for m in report.metrics if m.metric == "mean_score")
    assert mean_delta.delta == 0.0
    assert mean_delta.direction == "unchanged"
    assert report.new_failures == []
    assert report.new_passes == []


def test_positive_delta():
    ra = _run("a", mean_score=0.5, refusal_rate=0.7)
    rb = _run("b", mean_score=0.8, refusal_rate=0.9)
    report = compute_drift(ra, [], rb, [])
    mean_delta = next(m for m in report.metrics if m.metric == "mean_score")
    assert abs(mean_delta.delta - 0.3) < 0.001
    assert mean_delta.direction == "up"


def test_negative_delta():
    ra = _run("a", mean_score=0.9, refusal_rate=0.95)
    rb = _run("b", mean_score=0.6, refusal_rate=0.7)
    report = compute_drift(ra, [], rb, [])
    mean_delta = next(m for m in report.metrics if m.metric == "mean_score")
    assert mean_delta.direction == "down"


def test_flip_detection():
    ra = _run("a", mean_score=0.7, refusal_rate=0.8)
    rb = _run("b", mean_score=0.7, refusal_rate=0.8)
    # custom:1 passes in A (score=0.8, refusal correct), fails in B (score=0.2)
    results_a = [_result(ra.id, "custom:1", aggregate_score=0.8)]
    results_b = [_result(rb.id, "custom:1", aggregate_score=0.2)]
    report = compute_drift(ra, results_a, rb, results_b)
    assert "custom:1" in report.new_failures
    assert report.new_passes == []


def test_new_pass_detection():
    ra = _run("a")
    rb = _run("b")
    results_a = [_result(ra.id, "custom:1", aggregate_score=0.2)]
    results_b = [_result(rb.id, "custom:1", aggregate_score=0.9)]
    report = compute_drift(ra, results_a, rb, results_b)
    assert "custom:1" in report.new_passes
    assert report.new_failures == []


def test_empty_intersection():
    ra = _run("a", mean_score=0.7)
    rb = _run("b", mean_score=0.8)
    results_a = [_result(ra.id, "custom:only-a")]
    results_b = [_result(rb.id, "custom:only-b")]
    report = compute_drift(ra, results_a, rb, results_b)
    assert report.cases_in_a_only == 1
    assert report.cases_in_b_only == 1
    assert report.new_failures == []
    assert report.new_passes == []


def test_none_scores_handled():
    ra = _run("a", mean_score=None)
    rb = _run("b", mean_score=0.5)
    report = compute_drift(ra, [], rb, [])
    mean_delta = next(m for m in report.metrics if m.metric == "mean_score")
    assert mean_delta.delta is None
    assert mean_delta.direction == "unknown"
