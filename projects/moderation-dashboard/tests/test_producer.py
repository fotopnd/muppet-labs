from __future__ import annotations

import csv
from pathlib import Path

from moderation_dashboard.producer import (
    CATEGORY_PRIORITY,
    get_primary_category,
    load_jigsaw_csv,
)


def _make_csv(rows: list[dict]) -> Path:
    """Write rows to a temporary in-memory CSV and return a writable temp path."""
    import tempfile

    fieldnames = list(rows[0].keys())
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        return Path(f.name)


_BASE_ROW = {
    "id": "1",
    "comment_text": "Test comment",
    "toxic": "0",
    "severe_toxic": "0",
    "obscene": "0",
    "threat": "0",
    "insult": "0",
    "identity_hate": "0",
}


def test_get_primary_category_severe_toxic_wins():
    row = {**_BASE_ROW, "severe_toxic": "1", "toxic": "1", "obscene": "1"}
    assert get_primary_category(row) == "severe_toxic"


def test_get_primary_category_threat_priority():
    row = {**_BASE_ROW, "threat": "1", "insult": "1"}
    assert get_primary_category(row) == "threat"


def test_get_primary_category_clean():
    row = {**_BASE_ROW}
    assert get_primary_category(row) == "clean"


def test_get_primary_category_follows_priority_order():
    # All categories set — should return first in CATEGORY_PRIORITY
    row = {k: "1" for k in CATEGORY_PRIORITY}
    assert get_primary_category(row) == CATEGORY_PRIORITY[0]


def test_load_jigsaw_csv_returns_rows():
    path = _make_csv([{**_BASE_ROW, "comment_text": f"comment {i}"} for i in range(5)])
    rows = load_jigsaw_csv(path)
    assert len(rows) == 5


def test_load_jigsaw_csv_respects_limit():
    path = _make_csv([{**_BASE_ROW, "comment_text": f"comment {i}"} for i in range(10)])
    rows = load_jigsaw_csv(path, limit=3)
    assert len(rows) == 3


def test_load_jigsaw_csv_skips_empty_content():
    path = _make_csv(
        [
            {**_BASE_ROW, "comment_text": "valid"},
            {**_BASE_ROW, "comment_text": "   "},  # whitespace only
            {**_BASE_ROW, "comment_text": "also valid"},
        ]
    )
    rows = load_jigsaw_csv(path)
    assert len(rows) == 2


def test_load_jigsaw_csv_row_has_index():
    path = _make_csv([{**_BASE_ROW, "comment_text": "hello"}])
    rows = load_jigsaw_csv(path)
    assert "_idx" in rows[0]
    assert rows[0]["_idx"] == 0
