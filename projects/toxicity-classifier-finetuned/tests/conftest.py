from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture()
def tmp_data_dir(tmp_path: Path) -> Path:
    """Write a minimal Jigsaw-shaped CSV to a temp directory."""
    rows = [
        {
            "id": str(i),
            "comment_text": f"comment {i}",
            "toxic": i % 2,
            "severe_toxic": 0,
            "obscene": 0,
            "threat": 0,
            "insult": 0,
            "identity_hate": 0,
        }
        for i in range(40)
    ]
    df = pd.DataFrame(rows)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    df.to_csv(data_dir / "train.csv", index=False)
    return data_dir


@pytest.fixture()
def mock_distilbert_model():
    """Randomly-initialised DistilBERT-shaped model — no pretrained weights downloaded."""
    from transformers import AutoConfig, AutoModelForSequenceClassification

    config = AutoConfig.from_pretrained(
        "distilbert-base-uncased",
        num_labels=2,
        dim=64,
        n_layers=2,
        n_heads=2,
        hidden_dim=128,
    )
    return AutoModelForSequenceClassification.from_config(config)


@pytest.fixture()
def mock_roberta_model():
    """Randomly-initialised RoBERTa-shaped model — no pretrained weights downloaded."""
    from transformers import AutoConfig, AutoModelForSequenceClassification

    config = AutoConfig.from_pretrained(
        "roberta-base",
        num_labels=2,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=2,
        intermediate_size=128,
    )
    return AutoModelForSequenceClassification.from_config(config)


@pytest.fixture()
def mock_tokenizer():
    """Real DistilBERT tokenizer — vocab only, no model weights."""
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained("distilbert-base-uncased")
