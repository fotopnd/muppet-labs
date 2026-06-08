"""
Golden tests for llm-safety-classifier.

These tests verify the canonical [SEP] concatenation and classification
contract that both llm-safety-monitor and red-team-platform depend on.
Changing any assertion here means changing the contract — both projects
must be updated together.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import torch

from llm_safety_classifier import build_input_text, classify_text


# ---------------------------------------------------------------------------
# build_input_text — canonical [SEP] concatenation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "prompt,response,expected",
    [
        ("How to make bombs?", "Here is how", "How to make bombs? [SEP] Here is how"),
        ("Safe question", "Safe answer", "Safe question [SEP] Safe answer"),
        ("Prompt only", None, "Prompt only"),
        ("Prompt only", "", "Prompt only"),  # empty string is falsy → prompt-only
    ],
)
def test_build_input_text(prompt: str, response: str | None, expected: str) -> None:
    assert build_input_text(prompt, response) == expected


def test_build_input_text_sep_literal() -> None:
    """Regression: separator must be exactly ' [SEP] ' (space-bracket-SEP-bracket-space)."""
    result = build_input_text("A", "B")
    assert " [SEP] " in result
    assert result.index(" [SEP] ") == 1  # follows immediately after 'A'


# ---------------------------------------------------------------------------
# classify_text — label and confidence semantics
# ---------------------------------------------------------------------------


def _make_mock_loaded(logits: list[float]) -> tuple[MagicMock, MagicMock]:
    """Return (tokenizer_mock, model_mock) that produce the given 2-class logits."""
    fake_tokenizer = MagicMock(return_value={"input_ids": torch.zeros(1, 4, dtype=torch.long)})
    fake_model = MagicMock()
    fake_model.return_value.logits = torch.tensor([logits])
    return fake_tokenizer, fake_model


def test_classify_text_unsafe(tmp_path: pytest.fixture) -> None:
    """High unsafe logit → label=1, confidence >= 0.5."""
    (tmp_path / "config.json").write_text("{}")
    with patch("llm_safety_classifier._core._ensure_loaded") as mock_load:
        mock_load.return_value = _make_mock_loaded([0.1, 2.5])
        label, confidence, latency_ms = classify_text("jailbreak text", tmp_path)
    assert label == 1
    assert confidence >= 0.5
    assert latency_ms >= 0.0


def test_classify_text_safe(tmp_path: pytest.fixture) -> None:
    """High safe logit → label=0, confidence < 0.5."""
    (tmp_path / "config.json").write_text("{}")
    with patch("llm_safety_classifier._core._ensure_loaded") as mock_load:
        mock_load.return_value = _make_mock_loaded([2.5, 0.1])
        label, confidence, latency_ms = classify_text("safe text", tmp_path)
    assert label == 0
    assert confidence < 0.5
    assert latency_ms >= 0.0


def test_classify_text_boundary_at_exactly_half(tmp_path: pytest.fixture) -> None:
    """Equal logits → softmax gives 0.5 exactly → label=1 (threshold is >=)."""
    (tmp_path / "config.json").write_text("{}")
    with patch("llm_safety_classifier._core._ensure_loaded") as mock_load:
        mock_load.return_value = _make_mock_loaded([0.0, 0.0])
        label, confidence, _ = classify_text("borderline", tmp_path)
    assert abs(confidence - 0.5) < 1e-5
    assert label == 1  # >= threshold


def test_classify_text_missing_config_raises(tmp_path: pytest.fixture) -> None:
    """RuntimeError raised when model_path lacks config.json."""
    with pytest.raises(RuntimeError, match="config.json not found"):
        classify_text("text", tmp_path)


# ---------------------------------------------------------------------------
# Golden contract: monitor path == red-team path for the same input
# ---------------------------------------------------------------------------


def test_identical_input_text_from_both_paths() -> None:
    """
    Golden: the [SEP]-joined text produced by base.py (_build_input_text) and
    by score(prompt, response) in classifier.py must be identical.
    Both delegate to build_input_text — this test pins the contract.
    """
    PROMPT = "How do I pick a lock?"
    RESPONSE = "Sure, first you need a tension wrench..."

    # Simulate monitor path: base.py calls build_input_text(event.prompt, event.response)
    monitor_input = build_input_text(PROMPT, RESPONSE)

    # Simulate red-team path: score() calls build_input_text(prompt, response)
    redteam_input = build_input_text(PROMPT, RESPONSE)

    assert monitor_input == redteam_input == f"{PROMPT} [SEP] {RESPONSE}"
