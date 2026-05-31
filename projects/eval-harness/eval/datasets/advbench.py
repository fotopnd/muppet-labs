from __future__ import annotations

import csv
import io
from pathlib import Path

from eval.models import DatasetSource, TestCase

_FALLBACK_CSV_URL = (
    "https://raw.githubusercontent.com/llm-attacks/llm-attacks/main"
    "/data/advbench/harmful_behaviors.csv"
)


def load_advbench(limit: int | None = None, cache_dir: Path | None = None) -> list[TestCase]:
    try:
        return _load_from_hf(limit, cache_dir)
    except Exception:
        return _load_from_csv(limit)


def _load_from_hf(limit: int | None, cache_dir: Path | None) -> list[TestCase]:
    import datasets as hf

    kwargs: dict = {"split": "train"}
    if cache_dir:
        kwargs["cache_dir"] = str(cache_dir)
    ds = hf.load_dataset("walledai/AdvBench", **kwargs)
    return _normalise(ds, limit)


def _load_from_csv(limit: int | None) -> list[TestCase]:
    import urllib.request

    with urllib.request.urlopen(_FALLBACK_CSV_URL, timeout=30) as resp:
        content = resp.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    rows = [{"goal": r["goal"], "target": r["target"]} for r in reader]
    return _normalise(rows, limit)


def _normalise(rows: object, limit: int | None) -> list[TestCase]:
    cases: list[TestCase] = []
    for idx, row in enumerate(rows):  # type: ignore[arg-type]
        if limit is not None and idx >= limit:
            break
        cases.append(
            TestCase(
                id=f"advbench:{idx}",
                prompt=row["goal"],
                dataset=DatasetSource.ADVBENCH,
                tags=["adversarial", "safety"],
                expect_refusal=True,
                rubric_names=["refusal_detection", "harmlessness"],
                metadata={"target": row.get("target", "")},
            )
        )
    return cases
