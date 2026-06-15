"""Seed back_translation on all bias_divergence_scores rows that lack one."""
from __future__ import annotations

import asyncio
import logging

import anthropic
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.bias.models import BiasDivergenceScore, BiasResponse
from red_team_platform.config import get_settings
from red_team_platform.db import create_engine, create_session_factory

logger = logging.getLogger(__name__)

LANG_NAMES = {"zh": "Chinese", "ru": "Russian", "ar": "Arabic"}
MODEL = "claude-haiku-4-5-20251001"


async def _translate(client: anthropic.AsyncAnthropic, text: str, lang: str) -> str:
    lang_name = LANG_NAMES.get(lang, lang)
    msg = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Translate the following {lang_name} text to English. "
                    f"Return only the translation, no explanation:\n\n{text}"
                ),
            }
        ],
    )
    return msg.content[0].text if msg.content else ""


async def seed_back_translations(session: AsyncSession) -> int:
    settings = get_settings()
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or None)

    result = await session.execute(
        select(BiasDivergenceScore).where(BiasDivergenceScore.back_translation.is_(None))
    )
    pending = result.scalars().all()

    if not pending:
        logger.info("All back_translations already populated.")
        return 0

    logger.info("%d rows to back-translate", len(pending))
    written = 0

    for i, score in enumerate(pending):
        resp_result = await session.execute(
            select(BiasResponse).where(BiasResponse.id == score.other_response_id)
        )
        resp = resp_result.scalar_one_or_none()
        if resp is None or not resp.response_text.strip():
            continue

        try:
            translation = await _translate(client, resp.response_text, score.language)
        except Exception as exc:
            logger.warning("Translation failed for %s / %s: %s", score.probe_id, score.language, exc)
            continue

        await session.execute(
            update(BiasDivergenceScore)
            .where(BiasDivergenceScore.id == score.id)
            .values(back_translation=translation)
        )
        written += 1

        if (i + 1) % 10 == 0:
            await session.flush()
            logger.info("Progress: %d / %d", i + 1, len(pending))

    await session.flush()
    logger.info("Wrote %d back-translations", written)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    settings = get_settings()
    engine = create_engine(settings.database_url)
    factory = create_session_factory(engine)

    async def _run() -> None:
        async with factory() as session:
            written = await seed_back_translations(session)
            await session.commit()
        print(f"Done — {written} back-translations written.")

    asyncio.run(_run())
