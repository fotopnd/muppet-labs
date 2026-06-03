from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import torch

from toxicity_classifier.evaluate import (
    ModelMetrics,
    _compute_metrics,
    _predict_finetuned,
)


def test_compute_metrics_perfect_predictions() -> None:
    preds = [1, 0, 1, 0, 1]
    labels = [1, 0, 1, 0, 1]
    category_arrays = {"severe_toxic": [0, 0, 1, 0, 1], "obscene": [1, 0, 0, 0, 1]}
    m = _compute_metrics(preds, labels, category_arrays)
    assert m.f1 == pytest.approx(1.0)
    assert m.precision == pytest.approx(1.0)
    assert m.recall == pytest.approx(1.0)
    assert "severe_toxic" in m.per_category
    assert "obscene" in m.per_category


def test_compute_metrics_all_wrong() -> None:
    preds = [0, 0, 0, 0]
    labels = [1, 1, 1, 1]
    m = _compute_metrics(preds, labels, {})
    assert m.f1 == pytest.approx(0.0)
    assert m.recall == pytest.approx(0.0)


def test_predict_finetuned_returns_binary_list(mock_distilbert_model, mock_tokenizer) -> None:
    texts = ["comment one", "comment two", "comment three"]
    preds = _predict_finetuned(
        mock_distilbert_model, mock_tokenizer, texts, torch.device("cpu"), batch_size=2
    )
    assert len(preds) == 3
    assert all(p in (0, 1) for p in preds)


def test_evaluate_writes_json_and_returns_result(
    tmp_path: Path, tmp_data_dir: Path, mock_distilbert_model, mock_tokenizer
) -> None:
    """
    Patch from_pretrained and the zero-shot pipeline so evaluate() runs without
    downloading any model weights.
    """

    def mock_zero_shot(checkpoint, texts, batch_size=32):
        return [0] * len(texts)

    with (
        patch(
            "transformers.AutoModelForSequenceClassification.from_pretrained",
            return_value=mock_distilbert_model,
        ),
        patch(
            "transformers.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ),
        patch(
            "toxicity_classifier.evaluate._predict_zero_shot",
            side_effect=mock_zero_shot,
        ),
    ):
        from toxicity_classifier.evaluate import evaluate

        result = evaluate(
            checkpoint_dir=tmp_path / "fake-checkpoint",
            model_key="distilbert",
            data_dir=tmp_data_dir,
            output_dir=tmp_path / "eval_results",
        )

    assert result.model_slug == "distilbert-finetuned"
    assert result.test_size > 0
    assert isinstance(result.finetuned, ModelMetrics)
    assert isinstance(result.zero_shot_baseline, ModelMetrics)

    # JSON file must exist and be parseable
    result_files = list((tmp_path / "eval_results").glob("distilbert-finetuned-*.json"))
    assert len(result_files) == 1
    data = json.loads(result_files[0].read_text())
    assert "finetuned" in data
    assert "zero_shot_baseline" in data
    assert "test_size" in data
