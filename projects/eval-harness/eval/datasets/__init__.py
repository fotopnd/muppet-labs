from __future__ import annotations

from pathlib import Path

from eval.models import DatasetSource, RunConfig, TestCase


def load_dataset(
    source: DatasetSource,
    config: RunConfig,
    cases_path: Path | None = None,
    cache_dir: Path | None = None,
) -> list[TestCase]:
    limit = config.dataset_limit
    if source == DatasetSource.CUSTOM:
        from eval.datasets.custom import load_custom_cases

        if cases_path is None:
            raise ValueError("--cases PATH is required for the custom dataset")
        cases = load_custom_cases(cases_path)
        return cases[:limit] if limit else cases
    if source == DatasetSource.TRUTHFULQA:
        from eval.datasets.truthfulqa import load_truthfulqa

        return load_truthfulqa(limit=limit, cache_dir=cache_dir)
    if source == DatasetSource.ADVBENCH:
        from eval.datasets.advbench import load_advbench

        return load_advbench(limit=limit, cache_dir=cache_dir)
    raise ValueError(f"Unknown dataset source: {source}")
