from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from llm_safety_training.datasets import (
    CATEGORY_TO_IDX,
    NUM_HARM_CATEGORIES,
    WILDGUARD_CATEGORIES,
    WildGuardSplits,
    _extract_hhrlhf_pair,
    build_prompt_detector_dataset,
    split_wildguard,
)


def test_wildguard_categories_count() -> None:
    assert NUM_HARM_CATEGORIES == 13
    assert len(WILDGUARD_CATEGORIES) == 13


def test_category_to_idx_bijection() -> None:
    assert len(CATEGORY_TO_IDX) == NUM_HARM_CATEGORIES
    for name, idx in CATEGORY_TO_IDX.items():
        assert WILDGUARD_CATEGORIES[idx] == name


def test_extract_hhrlhf_pair_valid() -> None:
    field = "\n\nHuman: What is 2+2?\n\nAssistant: It is 4."
    result = _extract_hhrlhf_pair(field)
    assert result is not None
    assert "What is 2+2?" in result
    assert "[SEP]" in result
    assert "It is 4." in result


def test_extract_hhrlhf_pair_malformed() -> None:
    assert _extract_hhrlhf_pair("no human prefix here") is None
    assert _extract_hhrlhf_pair("") is None


def _make_fake_wg_dataset(n: int = 100) -> list[dict]:
    rows = []
    for i in range(n):
        rows.append({
            "prompt": f"prompt {i}",
            "response": f"response {i}",
            "response_harm_label": "harmful" if i % 3 == 0 else "unharmful",
            "subcategory": WILDGUARD_CATEGORIES[i % NUM_HARM_CATEGORIES] if i % 3 == 0 else None,
        })
    return rows


class _FakeDataset:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self):  # type: ignore[override]
        return iter(self._rows)

    def __getitem__(self, idx: int) -> dict:
        return self._rows[idx]


def test_split_wildguard_no_overlap() -> None:
    fake_rows = _make_fake_wg_dataset(200)
    fake_ds = _FakeDataset(fake_rows)

    with patch("llm_safety_training.datasets.load_dataset", return_value=fake_ds):
        splits = split_wildguard(seed=42)

    # Verify no shared texts between pair train and taxonomy train
    pair_set = set(splits.pair_train_texts)
    tax_set = set(splits.taxonomy_train_texts)
    assert len(pair_set & tax_set) == 0, "Pair and taxonomy training sets must not overlap"


def test_split_wildguard_produces_data() -> None:
    fake_rows = _make_fake_wg_dataset(200)
    fake_ds = _FakeDataset(fake_rows)

    with patch("llm_safety_training.datasets.load_dataset", return_value=fake_ds):
        splits = split_wildguard(seed=42)

    assert len(splits.pair_train_texts) > 0
    assert len(splits.taxonomy_train_texts) > 0
    assert len(splits.pair_eval_texts) > 0
    assert len(splits.taxonomy_eval_texts) > 0
    assert len(splits.pair_train_labels) == len(splits.pair_train_texts)
    assert all(v in (0, 1) for v in splits.pair_train_labels)
    assert all(len(v) == NUM_HARM_CATEGORIES for v in splits.taxonomy_train_labels)


def test_split_wildguard_pair_larger_than_taxonomy() -> None:
    fake_rows = _make_fake_wg_dataset(200)
    fake_ds = _FakeDataset(fake_rows)

    with patch("llm_safety_training.datasets.load_dataset", return_value=fake_ds):
        splits = split_wildguard(seed=42)

    # 70% allocation should be larger than 30%
    assert len(splits.pair_train_texts) > len(splits.taxonomy_train_texts)
