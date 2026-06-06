from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llm_safety_training.evaluate import EvalResult, _compute_calibration_bins


def test_calibration_bins_basic() -> None:
    confidences = [0.1, 0.15, 0.5, 0.55, 0.9, 0.95]
    labels = [0, 0, 1, 1, 1, 1]
    bins = _compute_calibration_bins(confidences, labels)
    assert len(bins) > 0
    for b in bins:
        assert 0.0 <= b.actual_positive_rate <= 1.0
        assert b.count > 0


def test_calibration_bins_empty() -> None:
    bins = _compute_calibration_bins([], [])
    assert bins == []


def test_calibration_bins_excludes_empty() -> None:
    # Only one bin populated
    confidences = [0.95]
    labels = [1]
    bins = _compute_calibration_bins(confidences, labels)
    assert len(bins) == 1
    assert bins[0].count == 1
    assert bins[0].actual_positive_rate == 1.0


def test_evaluate_binary_writes_json(tmp_path: Path) -> None:
    import torch

    fake_checkpoint = tmp_path / "checkpoint"
    fake_checkpoint.mkdir()

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = MagicMock(
        input_ids=torch.zeros(4, 10, dtype=torch.long),
        attention_mask=torch.ones(4, 10, dtype=torch.long),
    )
    mock_model = MagicMock()
    mock_logits = torch.tensor([[0.1, 0.9], [0.8, 0.2], [0.3, 0.7], [0.9, 0.1]])
    mock_model.return_value.logits = mock_logits
    mock_model.eval = MagicMock()

    output_dir = tmp_path / "evals"
    output_dir.mkdir()

    with (
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
        patch("llm_safety_training.evaluate.load_hhrlhf_binary", return_value=(["t"] * 4, [0, 1, 0, 1])),
        patch("llm_safety_training.evaluate.split_wildguard") as mock_split,
    ):
        mock_split.return_value = MagicMock(
            pair_eval_texts=[],
            pair_eval_labels=[],
        )
        from llm_safety_training.evaluate import evaluate

        result = evaluate("pair", fake_checkpoint, output_dir)

    assert isinstance(result, EvalResult)
    assert result.model_type == "pair"
    assert 0.0 <= result.f1 <= 1.0

    json_files = list(output_dir.glob("pair-*.json"))
    assert len(json_files) == 1
    data = json.loads(json_files[0].read_text())
    assert "f1" in data
    assert "calibration_bins" in data
