from __future__ import annotations

from unittest.mock import patch

from eval.models import (
    CriterionScore,
    DatasetSource,
    Rubric,
    RubricCriterion,
    ScoringMethod,
    TestCase,
)
from eval.runner import RunnerResponse
from eval.scorer import detect_refusal, score_heuristic, score_result


def _criterion(match: list[str] = (), fail: list[str] = ()) -> RubricCriterion:
    return RubricCriterion(
        name="test_criterion",
        description="d",
        match_patterns=list(match),
        fail_patterns=list(fail),
        judge_instruction="j",
        weight=1.0,
    )


def _case() -> TestCase:
    return TestCase(
        id="custom:x",
        prompt="test prompt",
        dataset=DatasetSource.CUSTOM,
        rubric_names=["test_rubric"],
    )


# ── detect_refusal ─────────────────────────────────────────────────────────────


def test_detect_refusal_positive():
    assert detect_refusal("I cannot help with that.")
    assert detect_refusal("I won't assist with this request.")
    assert detect_refusal("Against my guidelines to do so.")
    assert detect_refusal("I must decline this request.")


def test_detect_refusal_negative():
    assert not detect_refusal("Sure, here is the information you asked for.")
    assert not detect_refusal("This is a perfectly normal response.")


# ── score_heuristic ────────────────────────────────────────────────────────────


def test_heuristic_match_hit():
    c = _criterion(match=["hello world"])
    result = score_heuristic("Say hello world please", c, "rubric")
    assert result.passed is True
    assert result.score == 1.0


def test_heuristic_fail_hit():
    c = _criterion(fail=["bad word"])
    result = score_heuristic("This contains bad word here", c, "rubric")
    assert result.passed is False
    assert result.score == 0.0


def test_heuristic_fail_takes_precedence_over_match():
    c = _criterion(match=["good"], fail=["bad"])
    result = score_heuristic("good and bad both here", c, "rubric")
    assert result.passed is False


def test_heuristic_no_match():
    c = _criterion(match=["hello"], fail=["bye"])
    result = score_heuristic("Neither here", c, "rubric")
    assert result.passed is None
    assert result.score is None


def test_heuristic_case_insensitive():
    c = _criterion(match=["HELLO"])
    result = score_heuristic("say hello", c, "rubric")
    assert result.passed is True


# ── score_result ───────────────────────────────────────────────────────────────


def test_score_result_heuristic_only():
    case = _case()
    rubric = Rubric(
        name="test_rubric",
        description="d",
        scoring_method=ScoringMethod.HEURISTIC,
        criteria=[_criterion(match=["I cannot"])],
    )
    response = RunnerResponse(
        raw_text="I cannot help with that.",
        latency_ms=100,
        model_name="test",
        finish_reason="stop",
    )
    result = score_result(case, response, [rubric], "judge-model", skip_judge=True)
    assert result.refusal_detected is True
    assert len(result.criterion_scores) == 1
    assert result.criterion_scores[0].passed is True
    assert result.aggregate_score == 1.0


def test_score_result_no_rubrics():
    case = TestCase(
        id="custom:x",
        prompt="test",
        dataset=DatasetSource.CUSTOM,
        rubric_names=[],
    )
    response = RunnerResponse(
        raw_text="Some response.",
        latency_ms=50,
        model_name="test",
        finish_reason="stop",
    )
    result = score_result(case, response, [], "judge-model", skip_judge=True)
    assert result.criterion_scores == []
    assert result.aggregate_score is None


def test_score_result_weighted_aggregate():
    case = _case()
    rubric = Rubric(
        name="test_rubric",
        description="d",
        scoring_method=ScoringMethod.HEURISTIC,
        criteria=[
            RubricCriterion(
                name="c1",
                description="d",
                match_patterns=["pass"],
                fail_patterns=[],
                weight=2.0,
            ),
            RubricCriterion(
                name="c2",
                description="d",
                match_patterns=[],
                fail_patterns=["fail"],
                weight=1.0,
            ),
        ],
    )
    response = RunnerResponse(
        raw_text="pass and fail both here",
        latency_ms=100,
        model_name="test",
        finish_reason="stop",
    )
    result = score_result(case, response, [rubric], "judge", skip_judge=True)
    # c1: score=1.0 weight=2.0; c2: score=0.0 weight=1.0 → (1.0*2 + 0.0*1) / (2+1) = 0.667
    assert result.aggregate_score is not None
    assert abs(result.aggregate_score - 2 / 3) < 0.001


def test_score_result_run_id_propagated():
    case = _case()
    rubric = Rubric(
        name="test_rubric",
        description="d",
        scoring_method=ScoringMethod.HEURISTIC,
        criteria=[_criterion(match=["hi"])],
    )
    response = RunnerResponse(raw_text="hi", latency_ms=10, model_name="m", finish_reason="stop")
    result = score_result(case, response, [rubric], "judge", run_id="run-xyz", skip_judge=True)
    assert result.run_id == "run-xyz"


# ── BOTH-mode merge ────────────────────────────────────────────────────────────


def _both_rubric() -> Rubric:
    return Rubric(
        name="test_rubric",
        description="d",
        scoring_method=ScoringMethod.BOTH,
        criteria=[_criterion(match=["I cannot"], fail=[])],
    )


def _judge_score(
    passed: bool | None, score: float | None, rationale: str = "judge"
) -> CriterionScore:
    return CriterionScore(
        criterion_name="test_criterion",
        rubric_name="test_rubric",
        passed=passed,
        score=score,
        method=ScoringMethod.LLM_JUDGE,
        rationale=rationale,
    )


def test_both_mode_heuristic_passed_wins_over_judge():
    """When heuristic has a definitive passed, it overrides judge's passed."""
    case = _case()
    response = RunnerResponse(
        raw_text="I cannot help.",
        latency_ms=10,
        model_name="m",
        finish_reason="stop",
    )
    # heuristic: passed=True (match hit); judge: passed=False, score=0.0
    with patch("eval.scorer.score_llm_judge", return_value=_judge_score(False, 0.0)):
        result = score_result(case, response, [_both_rubric()], "judge-model")
    merged = result.criterion_scores[0]
    assert merged.method == ScoringMethod.BOTH
    assert merged.passed is True  # heuristic wins
    assert merged.score is not None
    assert abs(merged.score - 0.5) < 0.001  # (1.0 + 0.0) / 2


def test_both_mode_judge_passed_used_when_heuristic_inconclusive():
    """When heuristic is inconclusive (None), judge's passed is used."""
    case = _case()
    response = RunnerResponse(
        raw_text="No patterns match this.",
        latency_ms=10,
        model_name="m",
        finish_reason="stop",
    )
    # heuristic: passed=None (no match); judge: passed=True, score=0.9
    with patch("eval.scorer.score_llm_judge", return_value=_judge_score(True, 0.9)):
        result = score_result(case, response, [_both_rubric()], "judge-model")
    merged = result.criterion_scores[0]
    assert merged.passed is True  # judge used since heuristic is None
    assert merged.score == 0.9  # only judge score available


def test_both_mode_score_averaged_when_both_available():
    """Score is averaged when both heuristic and judge return values."""
    case = _case()
    response = RunnerResponse(
        raw_text="I cannot help.",
        latency_ms=10,
        model_name="m",
        finish_reason="stop",
    )
    # heuristic: score=1.0; judge: score=0.6
    with patch("eval.scorer.score_llm_judge", return_value=_judge_score(True, 0.6)):
        result = score_result(case, response, [_both_rubric()], "judge-model")
    merged = result.criterion_scores[0]
    assert abs(merged.score - 0.8) < 0.001  # (1.0 + 0.6) / 2


def test_both_mode_score_is_none_when_both_none():
    """aggregate_score is None when all scores are None."""
    case = _case()
    response = RunnerResponse(
        raw_text="No patterns match.",
        latency_ms=10,
        model_name="m",
        finish_reason="stop",
    )
    # heuristic: None; judge: None
    with patch("eval.scorer.score_llm_judge", return_value=_judge_score(None, None)):
        result = score_result(case, response, [_both_rubric()], "judge-model")
    assert result.aggregate_score is None
