from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import torch

from llm_safety_monitor.types import WILDGUARD_CATEGORIES


def _make_settings(tmp_path: Path):
    from llm_safety_monitor.config import Settings

    pair_path = tmp_path / "pair"
    pair_path.mkdir()
    prompt_path = tmp_path / "prompt"
    prompt_path.mkdir()
    taxonomy_path = tmp_path / "taxonomy"
    taxonomy_path.mkdir()

    return Settings(
        PAIR_CLASSIFIER_PATH=pair_path,
        PROMPT_DETECTOR_PATH=prompt_path,
        TAXONOMY_CLASSIFIER_PATH=taxonomy_path,
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SYNC_DATABASE_URL="sqlite:///:memory:",
        KAFKA_BOOTSTRAP_SERVERS="localhost:9092",
    )


def _mock_tokenizer_and_model(num_labels: int = 2):
    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = MagicMock(
        input_ids=torch.zeros(1, 10, dtype=torch.long),
        attention_mask=torch.ones(1, 10, dtype=torch.long),
    )
    mock_model = MagicMock()
    logits = torch.zeros(1, num_labels)
    logits[0][1] = 2.0  # push class 1 confidence high
    mock_model.return_value = MagicMock(logits=logits)
    mock_model.eval = MagicMock()
    return mock_tokenizer, mock_model


def test_pair_classifier_classify(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    mock_tokenizer, mock_model = _mock_tokenizer_and_model(num_labels=2)

    with (
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
    ):
        from llm_safety_monitor.consumers.pair_classifier import PairSafetyClassifier

        clf = PairSafetyClassifier(settings)
        result = clf.classify("some text")

    assert result["predicted_label"] in (0, 1)
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["latency_ms"] > 0
    assert result["taxonomy_labels"] is None


def test_prompt_detector_classify(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)
    mock_tokenizer, mock_model = _mock_tokenizer_and_model(num_labels=2)

    with (
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
    ):
        from llm_safety_monitor.consumers.prompt_detector import PromptAdversarialDetector

        clf = PromptAdversarialDetector(settings)
        result = clf.classify("benign prompt")

    assert result["predicted_label"] in (0, 1)
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["latency_ms"] > 0
    assert result["taxonomy_labels"] is None


def test_taxonomy_classifier_classify(tmp_path: Path) -> None:
    settings = _make_settings(tmp_path)

    mock_tokenizer = MagicMock()
    mock_tokenizer.return_value = MagicMock(
        input_ids=torch.zeros(1, 10, dtype=torch.long),
        attention_mask=torch.ones(1, 10, dtype=torch.long),
    )
    mock_model = MagicMock()
    scores = [2.0] + [-2.0] * (len(WILDGUARD_CATEGORIES) - 1)  # first category above threshold after sigmoid
    mock_model.return_value = MagicMock(logits=torch.tensor([scores]))
    mock_model.eval = MagicMock()

    with (
        patch("transformers.AutoTokenizer.from_pretrained", return_value=mock_tokenizer),
        patch("transformers.AutoModelForSequenceClassification.from_pretrained", return_value=mock_model),
    ):
        from llm_safety_monitor.consumers.taxonomy_classifier import HarmTaxonomyClassifier

        clf = HarmTaxonomyClassifier(settings)
        result = clf.classify("harmful text about violence")

    assert result["predicted_label"] == 1
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["latency_ms"] > 0
    assert isinstance(result["taxonomy_labels"], list)
    assert len(result["taxonomy_labels"]) >= 1


def test_consumer_raises_if_no_checkpoint(tmp_path: Path) -> None:
    from llm_safety_monitor.config import Settings

    settings = Settings(
        PAIR_CLASSIFIER_PATH=tmp_path / "nonexistent",
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SYNC_DATABASE_URL="sqlite:///:memory:",
        KAFKA_BOOTSTRAP_SERVERS="localhost:9092",
    )
    with pytest.raises(RuntimeError, match="not found"):
        from llm_safety_monitor.consumers.pair_classifier import PairSafetyClassifier

        PairSafetyClassifier(settings)
