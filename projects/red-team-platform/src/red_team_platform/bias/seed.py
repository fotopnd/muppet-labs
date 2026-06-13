from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.bias.models import BiasProbe, BiasPromptVariant

logger = logging.getLogger(__name__)

_CORPUS_PATH = Path(__file__).parent / "data" / "bias-corpus.json"
_TOPIC_ID_RE = re.compile(r"^[a-z]{2}_\d{2}$")

LANGUAGES: list[str] = ["en", "zh", "ru", "ar"]


class BiasCorpusEntry(BaseModel):
    topic_id: str
    government: str
    label: str
    probe_question_en: str
    probe_question_zh: str | None = None
    probe_question_ru: str | None = None
    probe_question_ar: str | None = None
    divergence_hypothesis: str

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, v: str) -> str:
        if not _TOPIC_ID_RE.match(v):
            raise ValueError(f"topic_id must match ^[a-z]{{2}}_\\d{{2}}$, got {v!r}")
        return v

    @field_validator("probe_question_en")
    @classmethod
    def validate_en_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("probe_question_en must not be empty")
        return v

    def prompt_for_language(self, language: str) -> str | None:
        return getattr(self, f"probe_question_{language}", None)


def load_corpus(path: Path = _CORPUS_PATH) -> list[BiasCorpusEntry]:
    """
    Reads bias-corpus.json (array of {government, topics[]} objects),
    flattens to a list of BiasCorpusEntry, and validates each entry.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    entries: list[BiasCorpusEntry] = []
    for gov_block in raw:
        government = gov_block["government"]
        for topic in gov_block["topics"]:
            entry = BiasCorpusEntry(government=government, **topic)
            entries.append(entry)
    return entries


async def seed_bias_corpus(
    session: AsyncSession,
    entries: list[BiasCorpusEntry],
) -> tuple[int, int, int]:
    """
    Upserts BiasProbe rows (ON CONFLICT DO NOTHING — corpus is static).
    Then upserts BiasPromptVariant rows for all non-null language fields.
    Returns (probes_upserted, variants_upserted, variants_skipped_null).
    """
    probes_upserted = 0
    variants_upserted = 0
    variants_skipped = 0

    for entry in entries:
        # Upsert probe row
        probe_stmt = (
            insert(BiasProbe)
            .values(
                topic_id=entry.topic_id,
                government=entry.government,
                label=entry.label,
                probe_question_en=entry.probe_question_en,
                divergence_hypothesis=entry.divergence_hypothesis,
            )
            .on_conflict_do_nothing(index_elements=["topic_id"])
            .returning(BiasProbe.id)
        )
        result = await session.execute(probe_stmt)
        probe_row = result.fetchone()
        if probe_row is None:
            # Already existed — fetch its ID
            existing = await session.scalar(
                select(BiasProbe).where(BiasProbe.topic_id == entry.topic_id)
            )
            probe_id = existing.id  # type: ignore[union-attr]
        else:
            probe_id = probe_row[0]
            probes_upserted += 1

        # Upsert variant rows for each language
        for lang in LANGUAGES:
            prompt_text = entry.prompt_for_language(lang)
            if prompt_text is None:
                logger.warning(
                    "Skipping null variant: topic_id=%s language=%s", entry.topic_id, lang
                )
                variants_skipped += 1
                continue

            variant_stmt = (
                insert(BiasPromptVariant)
                .values(probe_id=probe_id, language=lang, prompt_text=prompt_text)
                .on_conflict_do_nothing(
                    index_elements=["probe_id", "language"],
                )
            )
            variant_result = await session.execute(variant_stmt)
            if variant_result.rowcount > 0:
                variants_upserted += 1

        await session.flush()

    return probes_upserted, variants_upserted, variants_skipped


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory

    settings = get_settings()
    entries = load_corpus()
    logger.info("Loaded %d corpus entries", len(entries))

    async def _run() -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        async with factory() as session:
            probes, variants, skipped = await seed_bias_corpus(session, entries)
            await session.commit()
        await engine.dispose()
        print(
            f"Seeded {probes} new probes, {variants} new variants. "
            f"Skipped {skipped} null language fields."
        )

    asyncio.run(_run())
