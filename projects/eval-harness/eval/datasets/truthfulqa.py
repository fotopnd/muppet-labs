from __future__ import annotations

from pathlib import Path

from eval.models import DatasetSource, TestCase


def load_truthfulqa(limit: int | None = None, cache_dir: Path | None = None) -> list[TestCase]:
    # Deferred import — datasets has a slow startup cost
    import datasets as hf

    kwargs: dict = {"split": "validation"}
    if cache_dir:
        kwargs["cache_dir"] = str(cache_dir)
    ds = hf.load_dataset("truthful_qa", "generation", **kwargs)

    cases: list[TestCase] = []
    for idx, row in enumerate(ds):
        if limit is not None and idx >= limit:
            break
        cases.append(
            TestCase(
                id=f"truthfulqa:{idx}",
                prompt=row["question"],
                dataset=DatasetSource.TRUTHFULQA,
                tags=["truthfulness"],
                reference_answer=row["best_answer"],
                expect_refusal=False,
                rubric_names=["truthfulness"],
                metadata={"correct_answers": row.get("correct_answers", [])},
            )
        )
    return cases
