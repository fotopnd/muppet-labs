from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, PrivateAttr, model_validator


class ModelBackend(StrEnum):
    LOCAL = "local"
    MLX = "mlx"
    CLAUDE = "claude"


class DatasetSource(StrEnum):
    CUSTOM = "custom"
    TRUTHFULQA = "truthfulqa"
    ADVBENCH = "advbench"


class ScoringMethod(StrEnum):
    HEURISTIC = "heuristic"
    LLM_JUDGE = "llm_judge"
    BOTH = "both"


class TestCase(BaseModel):
    id: str
    prompt: str
    dataset: DatasetSource
    tags: list[str] = Field(default_factory=list)
    reference_answer: str | None = None
    expect_refusal: bool = False
    rubric_names: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RubricCriterion(BaseModel):
    name: str
    description: str
    match_patterns: list[str] = Field(default_factory=list)
    fail_patterns: list[str] = Field(default_factory=list)
    judge_instruction: str = ""
    weight: float = 1.0

    _compiled_match: list[re.Pattern] = PrivateAttr(default_factory=list)
    _compiled_fail: list[re.Pattern] = PrivateAttr(default_factory=list)

    @model_validator(mode="after")
    def _compile_patterns(self) -> RubricCriterion:
        self._compiled_match = [re.compile(p, re.IGNORECASE) for p in self.match_patterns]
        self._compiled_fail = [re.compile(p, re.IGNORECASE) for p in self.fail_patterns]
        return self


class Rubric(BaseModel):
    name: str
    description: str
    scoring_method: ScoringMethod = ScoringMethod.BOTH
    criteria: list[RubricCriterion]


class RunConfig(BaseModel):
    model_backend: ModelBackend
    model_name: str
    endpoint_url: str | None = None
    dataset_names: list[DatasetSource]
    rubric_names: list[str]
    judge_model: str = "claude-sonnet-4-6"
    max_tokens: int = 512
    temperature: float = 0.0
    dataset_limit: int | None = None
    run_label: str | None = None


class CriterionScore(BaseModel):
    criterion_name: str
    rubric_name: str
    passed: bool | None
    score: float | None
    method: ScoringMethod
    rationale: str = ""


class EvalResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    run_id: str
    case_id: str
    prompt: str
    raw_response: str
    latency_ms: int
    refusal_detected: bool
    expect_refusal: bool = False
    criterion_scores: list[CriterionScore] = Field(default_factory=list)
    aggregate_score: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvalRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: RunConfig
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None
    total_cases: int = 0
    status: str = "running"
    mean_score: float | None = None
    refusal_rate: float | None = None


class MetricDelta(BaseModel):
    metric: str
    run_a_value: float | None
    run_b_value: float | None
    delta: float | None
    direction: str


class DriftReport(BaseModel):
    run_a_id: str
    run_b_id: str
    run_a_label: str | None
    run_b_label: str | None
    cases_in_a_only: int = 0
    cases_in_b_only: int = 0
    metrics: list[MetricDelta]
    rubric_deltas: dict[str, list[MetricDelta]]
    dataset_deltas: dict[str, list[MetricDelta]]
    new_failures: list[str]
    new_passes: list[str]
