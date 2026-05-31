from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from eval.datasets.custom import load_custom_cases
from eval.models import DatasetSource


def test_load_custom_cases_valid(tmp_path: Path):
    data = [
        {
            "id": "custom:001",
            "prompt": "What is 2+2?",
            "dataset": "custom",
            "tags": ["math"],
            "expect_refusal": False,
            "rubric_names": [],
        }
    ]
    f = tmp_path / "cases.yaml"
    f.write_text(yaml.dump(data))
    cases = load_custom_cases(f)
    assert len(cases) == 1
    assert cases[0].id == "custom:001"
    assert cases[0].dataset == DatasetSource.CUSTOM


def test_load_custom_cases_multiple(tmp_path: Path):
    data = [{"id": f"custom:{i}", "prompt": f"prompt {i}", "dataset": "custom"} for i in range(5)]
    f = tmp_path / "cases.yaml"
    f.write_text(yaml.dump(data))
    cases = load_custom_cases(f)
    assert len(cases) == 5


def test_load_custom_cases_invalid_raises(tmp_path: Path):
    data = [{"id": "x", "prompt": "p", "dataset": "invalid_source"}]
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.dump(data))
    with pytest.raises(ValueError, match="case\\[0\\]"):
        load_custom_cases(f)


def test_load_custom_cases_not_a_list(tmp_path: Path):
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.dump({"key": "value"}))
    with pytest.raises(ValueError, match="expected a YAML list"):
        load_custom_cases(f)


def test_load_custom_cases_missing_field(tmp_path: Path):
    data = [{"id": "custom:x", "dataset": "custom"}]  # missing prompt
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.dump(data))
    with pytest.raises(ValueError, match="case\\[0\\]"):
        load_custom_cases(f)
