import argparse
import asyncio
import logging

import anthropic
from sqlalchemy import select

from error_hide_seek.agents.red_team import plant_error
from error_hide_seek.config import settings
from error_hide_seek.db import AsyncSessionLocal, init_db
from error_hide_seek.models import CATEGORY_CYCLE, ErrorCategory, ExperimentPaper, Paper, PlantedError

log = logging.getLogger(__name__)


async def _run(experiment_id: int, category_override: ErrorCategory | None) -> None:
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set")

    await init_db()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(ExperimentPaper, Paper)
                .join(Paper, Paper.id == ExperimentPaper.paper_id)
                .where(ExperimentPaper.experiment_id == experiment_id)
            )
        ).all()

        if not rows:
            print(f"No papers found for experiment_id={experiment_id}")
            return

        existing_ids = set(
            (
                await session.scalars(
                    select(PlantedError.paper_id).where(PlantedError.experiment_id == experiment_id)
                )
            ).all()
        )

        total = len(rows)
        planted = 0
        skipped = 0

        for idx, (ep, paper) in enumerate(rows):
            if paper.id in existing_ids:
                skipped += 1
                continue

            # Use the category stored at experiment creation time.
            # Fall back to round-robin cycle for legacy rows where intended_category is NULL.
            if category_override:
                category = category_override
            elif ep.intended_category:
                category = ErrorCategory(ep.intended_category)
            else:
                category = ErrorCategory(CATEGORY_CYCLE[idx % len(CATEGORY_CYCLE)])

            log.info(
                "[%d/%d] paper_id=%d category=%s — planting", idx + 1, total, paper.id, category
            )

            result = await plant_error(client, paper.abstract, category)
            altered_abstract = paper.abstract.replace(result.original_text, result.altered_text, 1)

            session.add(
                PlantedError(
                    paper_id=paper.id,
                    experiment_id=experiment_id,
                    category=category,
                    original_text=result.original_text,
                    altered_text=result.altered_text,
                    altered_abstract=altered_abstract,
                    rationale=result.rationale,
                )
            )
            await session.flush()
            planted += 1
            print(f"[{idx + 1}/{total}] paper_id={paper.id} category={category} — done")

        await session.commit()

    print(f"Planted {planted} errors, skipped {skipped} (already planted).")


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Plant errors into experiment papers")
    parser.add_argument("--experiment-id", type=int, required=True)
    parser.add_argument(
        "--category",
        choices=[c.value for c in ErrorCategory],
        default=None,
    )
    args = parser.parse_args()
    category = ErrorCategory(args.category) if args.category else None
    asyncio.run(_run(args.experiment_id, category))
