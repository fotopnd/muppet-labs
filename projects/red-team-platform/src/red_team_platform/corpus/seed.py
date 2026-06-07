from __future__ import annotations

import asyncio
import logging

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.corpus.loader import AttackRecord, load_sevdeawesome
from red_team_platform.models import Attack
from red_team_platform.runner.taxonomy_classifier import (
    classify_category,
    get_taxonomy_classifier,
)

logger = logging.getLogger(__name__)


async def seed_corpus(
    session: AsyncSession,
    records: list[AttackRecord],
) -> tuple[int, int]:
    """
    For each record: classifies harm_goal → harm_category, then upserts into attacks table.
    Returns (inserted_count, updated_count).
    Taxonomy classifier must already be loaded before calling.
    """
    inserted = 0
    updated = 0

    for i, record in enumerate(records):
        harm_category = classify_category(record.harm_goal)
        record.harm_category = harm_category

        stmt = (
            insert(Attack)
            .values(
                source=record.source,
                source_id=record.source_id,
                harm_category=record.harm_category,
                strategy=record.strategy,
                attack_text=record.attack_text,
            )
            .on_conflict_do_update(
                index_elements=["source", "source_id"],
                set_={
                    "harm_category": record.harm_category,
                    "strategy": record.strategy,
                    "attack_text": record.attack_text,
                },
            )
            .returning(text("xmax"))  # xmax=0 means inserted; >0 means updated
        )
        result = await session.execute(stmt)
        row = result.fetchone()
        if row and row[0] == 0:
            inserted += 1
        else:
            updated += 1

        if (i + 1) % 100 == 0:
            logger.info("Seeded %d / %d attacks...", i + 1, len(records))
            await session.flush()

    return inserted, updated


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory

    settings = get_settings()

    # Fail fast if taxonomy classifier path is invalid
    get_taxonomy_classifier(settings.taxonomy_classifier_path)

    records = load_sevdeawesome()
    logger.info("Loaded %d attack records from sevdeawesome", len(records))

    async def _run() -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            inserted, updated = await seed_corpus(session, records)
            await session.commit()
        await engine.dispose()
        print(f"Seeded {inserted} new attacks, updated {updated} existing.")

    asyncio.run(_run())
