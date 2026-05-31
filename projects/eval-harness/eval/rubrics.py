from __future__ import annotations

from pathlib import Path

import yaml

from eval.models import Rubric, TestCase


def load_rubric(path: Path) -> Rubric:
    with path.open() as f:
        data = yaml.safe_load(f)
    try:
        return Rubric.model_validate(data)
    except Exception as exc:
        raise ValueError(f"Invalid rubric file {path}: {exc}") from exc


def load_rubrics(paths: list[Path]) -> dict[str, Rubric]:
    rubrics: dict[str, Rubric] = {}
    for path in paths:
        rubric = load_rubric(path)
        if rubric.name in rubrics:
            raise ValueError(f"Duplicate rubric name '{rubric.name}' from {path}")
        rubrics[rubric.name] = rubric
    return rubrics


def find_rubric_file(name: str, search_dirs: list[Path]) -> Path:
    for d in search_dirs:
        candidate = d / f"{name}.yaml"
        if candidate.exists():
            return candidate
    searched = ", ".join(str(d) for d in search_dirs)
    raise FileNotFoundError(f"Rubric '{name}.yaml' not found in: {searched}")


def get_applicable_rubrics(case: TestCase, all_rubrics: dict[str, Rubric]) -> list[Rubric]:
    return [all_rubrics[name] for name in case.rubric_names if name in all_rubrics]
