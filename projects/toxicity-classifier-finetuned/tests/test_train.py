from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import torch


def test_distilbert_forward_pass_and_loss(mock_distilbert_model, mock_tokenizer) -> None:
    """Confirm mock model produces finite loss on a tiny batch — no weight download needed."""
    texts = ["toxic comment", "nice comment"]
    enc = mock_tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=32)
    labels = torch.tensor([1, 0])
    output = mock_distilbert_model(**enc, labels=labels)
    assert output.loss is not None
    assert torch.isfinite(output.loss)


def test_roberta_forward_pass_and_loss(mock_roberta_model, mock_tokenizer) -> None:
    texts = ["you are terrible", "have a great day"]
    enc = mock_tokenizer(texts, return_tensors="pt", padding=True, truncation=True, max_length=32)
    labels = torch.tensor([1, 0])
    output = mock_roberta_model(**enc, labels=labels)
    assert output.loss is not None
    assert torch.isfinite(output.loss)


def test_train_distilbert_creates_checkpoint(
    tmp_path: Path, tmp_data_dir: Path, mock_distilbert_model, mock_tokenizer
) -> None:
    """
    Patch from_pretrained at the transformers source — the training modules defer
    their imports inside train(), so the module-level path doesn't exist.
    """
    with (
        patch(
            "transformers.AutoModelForSequenceClassification.from_pretrained",
            return_value=mock_distilbert_model,
        ),
        patch(
            "transformers.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ),
    ):
        from toxicity_classifier.train_distilbert import train

        checkpoint = train(
            data_dir=tmp_data_dir,
            output_dir=tmp_path / "out",
            epochs=1,
            batch_size=2,
            max_train_samples=8,
        )

    assert checkpoint.exists()
    assert (checkpoint / "config.json").exists()
    assert (tmp_path / "out" / "distilbert-train-log.json").exists()


def test_train_roberta_creates_checkpoint(
    tmp_path: Path, tmp_data_dir: Path, mock_roberta_model, mock_tokenizer
) -> None:
    with (
        patch(
            "transformers.AutoModelForSequenceClassification.from_pretrained",
            return_value=mock_roberta_model,
        ),
        patch(
            "transformers.AutoTokenizer.from_pretrained",
            return_value=mock_tokenizer,
        ),
    ):
        from toxicity_classifier.train_roberta import train

        checkpoint = train(
            data_dir=tmp_data_dir,
            output_dir=tmp_path / "out",
            epochs=1,
            batch_size=2,
            max_train_samples=8,
        )

    assert checkpoint.exists()
    assert (checkpoint / "config.json").exists()
    assert (tmp_path / "out" / "roberta-train-log.json").exists()
