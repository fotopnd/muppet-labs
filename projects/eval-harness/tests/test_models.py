from __future__ import annotations

import pytest
from pydantic import ValidationError

from eval.models import (
    DatasetSource,
    EvalResult,
    ModelBackend,
    RubricCriterion,
    RunConfig,
    TestCase,
)


def test_test_case_requires_id_and_prompt():
    with pytest.raises(ValidationError):
        TestCase.model_validate({"dataset": "custom"})  # missing id and prompt


def test_test_case_defaults():
    case = TestCase(id="x:1", prompt="p", dataset=DatasetSource.CUSTOM)
    assert case.tags == []
    assert case.rubric_names == []
    assert case.expect_refusal is False
    assert case.reference_answer is None


def test_rubric_criterion_compiles_patterns():
    c = RubricCriterion(
        name="test",
        description="d",
        match_patterns=["hello"],
        fail_patterns=["bad"],
    )
    assert len(c._compiled_match) == 1
    assert c._compiled_match[0].search("say hello world")
    assert len(c._compiled_fail) == 1
    assert c._compiled_fail[0].search("this is bad")


def test_run_config_defaults():
    rc = RunConfig(
        model_backend=ModelBackend.LOCAL,
        model_name="qwen",
        dataset_names=[DatasetSource.CUSTOM],
        rubric_names=[],
    )
    assert rc.temperature == 0.0
    assert rc.max_tokens == 512
    assert rc.judge_model == "claude-sonnet-4-6"


def test_eval_result_auto_id():
    r1 = EvalResult(
        run_id="run1",
        case_id="c1",
        prompt="p",
        raw_response="r",
        latency_ms=100,
        refusal_detected=False,
    )
    r2 = EvalResult(
        run_id="run1",
        case_id="c2",
        prompt="p",
        raw_response="r",
        latency_ms=100,
        refusal_detected=False,
    )
    assert r1.id != r2.id
    assert len(r1.id) == 36  # UUID format
