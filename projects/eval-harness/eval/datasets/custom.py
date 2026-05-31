from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from eval.models import TestCase


def load_custom_cases(path: Path) -> list[TestCase]:
    with path.open() as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, list):
        raise ValueError(f"{path}: expected a YAML list, got {type(raw).__name__}")
    cases: list[TestCase] = []
    for i, item in enumerate(raw):
        try:
            cases.append(TestCase.model_validate(item))
        except ValidationError as exc:
            raise ValueError(f"case[{i}]: {exc}") from exc
    return cases
