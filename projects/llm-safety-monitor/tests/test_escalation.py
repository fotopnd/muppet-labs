from __future__ import annotations

import pytest

from llm_safety_monitor.escalation.router import compute_escalation_reason
from llm_safety_monitor.types import EscalationReason


def test_jailbreak() -> None:
    reason = compute_escalation_reason(
        pair_label=1, pair_conf=0.9,
        prompt_label=1, prompt_conf=0.8,
        taxonomy_labels=["Hate"],
        has_response=True,
    )
    assert reason == EscalationReason.JAILBREAK


def test_benign_harmful() -> None:
    reason = compute_escalation_reason(
        pair_label=1, pair_conf=0.9,
        prompt_label=0, prompt_conf=0.1,
        taxonomy_labels=[],
        has_response=True,
    )
    assert reason == EscalationReason.BENIGN_HARMFUL


def test_log_only() -> None:
    reason = compute_escalation_reason(
        pair_label=0, pair_conf=0.1,
        prompt_label=1, prompt_conf=0.95,
        taxonomy_labels=[],
        has_response=True,
    )
    assert reason == EscalationReason.LOG_ONLY


def test_model_disagreement_pair_safe_taxonomy_flagged() -> None:
    reason = compute_escalation_reason(
        pair_label=0, pair_conf=0.1,
        prompt_label=0, prompt_conf=0.1,
        taxonomy_labels=["Violence"],
        has_response=True,
    )
    assert reason == EscalationReason.MODEL_DISAGREEMENT


def test_benign_harmful_pair_unsafe_prompt_safe() -> None:
    reason = compute_escalation_reason(
        pair_label=1, pair_conf=0.9,
        prompt_label=0, prompt_conf=0.1,
        taxonomy_labels=[],
        has_response=True,
    )
    # pair=1 + prompt=0 → BENIGN_HARMFUL (takes precedence over disagreement check)
    assert reason == EscalationReason.BENIGN_HARMFUL


def test_adversarial_prompt_flagged_no_response() -> None:
    reason = compute_escalation_reason(
        pair_label=0, pair_conf=0.0,
        prompt_label=1, prompt_conf=0.85,
        taxonomy_labels=[],
        has_response=False,
    )
    assert reason == EscalationReason.ADVERSARIAL_PROMPT_FLAGGED


def test_no_escalation_benign_safe() -> None:
    reason = compute_escalation_reason(
        pair_label=0, pair_conf=0.1,
        prompt_label=0, prompt_conf=0.05,
        taxonomy_labels=[],
        has_response=True,
    )
    assert reason is None


def test_prompt_only_below_threshold_no_escalation() -> None:
    reason = compute_escalation_reason(
        pair_label=0, pair_conf=0.0,
        prompt_label=1, prompt_conf=0.5,  # below 0.7 threshold
        taxonomy_labels=[],
        has_response=False,
    )
    assert reason is None
