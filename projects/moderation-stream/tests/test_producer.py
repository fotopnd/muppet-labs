from __future__ import annotations

from pathlib import Path

import pytest

from moderation_stream.producer import load_jigsaw_csv
from moderation_stream.types import ModerationEvent

SAMPLE_CSV = """\
id,comment_text,toxic,severe_toxic,obscene,threat,insult,identity_hate
1,"Hello world",0,0,0,0,0,0
2,"You are terrible",1,0,0,0,1,0
3,"Great post",0,0,0,0,0,0
"""


def test_load_basic(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=None))
    assert len(events) == 3
    assert all(isinstance(e, ModerationEvent) for e in events)


def test_load_limit(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=1))
    assert len(events) == 1


def test_label_assignment(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=None))
    assert events[0].label == 0
    assert events[1].label == 1


def test_event_ids_unique(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=None))
    ids = [e.event_id for e in events]
    assert len(ids) == len(set(ids))


def test_event_id_is_uuid_format(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=1))
    assert len(events[0].event_id) == 36
    assert events[0].event_id.count("-") == 4


def test_label_detail_populated(tmp_path: Path) -> None:
    f = tmp_path / "train.csv"
    f.write_text(SAMPLE_CSV)
    events = list(load_jigsaw_csv(f, limit=1))
    assert events[0].label_detail is not None
    assert "toxic" in events[0].label_detail


def test_label_is_optional_without_toxic_column(tmp_path: Path) -> None:
    csv_no_label = "id,comment_text\n1,Hello\n"
    f = tmp_path / "train.csv"
    f.write_text(csv_no_label)
    events = list(load_jigsaw_csv(f, limit=None))
    assert events[0].label is None
    assert events[0].label_detail is None
