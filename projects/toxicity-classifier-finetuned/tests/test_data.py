from __future__ import annotations

from pathlib import Path

import pytest

from toxicity_classifier.data import LABEL_COLUMNS, get_splits, load_jigsaw, tokenise_splits


def test_load_jigsaw_returns_dataframe(tmp_data_dir: Path) -> None:
    df = load_jigsaw(tmp_data_dir)
    assert len(df) == 40
    assert "comment_text" in df.columns
    assert "toxic" in df.columns


def test_load_jigsaw_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="train.csv"):
        load_jigsaw(tmp_path / "nonexistent")


def test_load_jigsaw_missing_columns_raises(tmp_path: Path) -> None:
    import pandas as pd

    bad_dir = tmp_path / "bad"
    bad_dir.mkdir()
    pd.DataFrame({"comment_text": ["hi"], "toxic": [0]}).to_csv(bad_dir / "train.csv", index=False)
    with pytest.raises(ValueError, match="missing required columns"):
        load_jigsaw(bad_dir)


def test_get_splits_sizes(tmp_data_dir: Path) -> None:
    df = load_jigsaw(tmp_data_dir)
    splits = get_splits(df)
    total = len(splits.train) + len(splits.val) + len(splits.test)
    assert total == 40
    # train ~80%, val ~10%, test ~10% — allow 1-row rounding tolerance
    assert len(splits.test) in (3, 4, 5)
    assert len(splits.val) in (3, 4, 5)


def test_get_splits_max_train_samples(tmp_data_dir: Path) -> None:
    df = load_jigsaw(tmp_data_dir)
    splits = get_splits(df, max_train_samples=5)
    assert len(splits.train) == 5


def test_get_splits_label_columns(tmp_data_dir: Path) -> None:
    df = load_jigsaw(tmp_data_dir)
    splits = get_splits(df)
    assert splits.label_columns == LABEL_COLUMNS


def test_tokenise_splits_output_shape(tmp_data_dir: Path, mock_tokenizer) -> None:
    df = load_jigsaw(tmp_data_dir)
    splits = get_splits(df)
    tok_splits = tokenise_splits(splits, mock_tokenizer)

    # Each split should have input_ids and attention_mask
    train_item = tok_splits.train[0]
    assert "input_ids" in train_item
    assert "attention_mask" in train_item
    assert "labels" in train_item
    assert len(train_item["input_ids"]) == 128


def test_tokenise_splits_test_retains_category_columns(tmp_data_dir: Path, mock_tokenizer) -> None:
    df = load_jigsaw(tmp_data_dir)
    splits = get_splits(df)
    tok_splits = tokenise_splits(splits, mock_tokenizer)

    # Category columns must survive into the test split for per-category eval
    test_cols = tok_splits.test.column_names
    for col in ["severe_toxic", "obscene", "threat", "insult", "identity_hate"]:
        assert col in test_cols, f"Column {col!r} missing from test split after tokenisation"
