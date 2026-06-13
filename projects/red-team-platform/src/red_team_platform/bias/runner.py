from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.bias.models import BiasPromptVariant, BiasResponse
from red_team_platform.runner.ollama_client import chat, make_client

logger = logging.getLogger(__name__)


async def run_bias_session(
    session: AsyncSession,
    language: str,
    model_name: str,
    ollama_base_url: str,
    ollama_timeout_s: int,
) -> int:
    """
    Queries bias_prompt_variants for the given language.
    Skips any variant that already has a BiasResponse for (variant_id, model_name).
    Fires remaining variants at Ollama, writes BiasResponse rows.
    Returns count of new responses written.
    """
    stmt = select(BiasPromptVariant).where(BiasPromptVariant.language == language)
    result = await session.execute(stmt)
    variants = result.scalars().all()

    if not variants:
        logger.warning(
            "No bias_prompt_variants found for language=%s. Run seed-bias-corpus first.",
            language,
        )
        return 0

    logger.info("Found %d variants for language=%s", len(variants), language)
    written = 0

    async with make_client(ollama_base_url, ollama_timeout_s) as client:
        for i, variant in enumerate(variants):
            # Idempotency: skip if already scored for this model
            existing = await session.scalar(
                select(BiasResponse).where(
                    BiasResponse.variant_id == variant.id,
                    BiasResponse.model_name == model_name,
                )
            )
            if existing is not None:
                logger.debug("Skipping variant %s (already scored)", variant.id)
                continue

            try:
                response_text, latency_ms = await chat(client, model_name, variant.prompt_text)
            except Exception as exc:
                logger.warning(
                    "Variant %s (lang=%s) failed: %s",
                    variant.id,
                    language,
                    exc,
                    exc_info=True,
                )
                continue

            session.add(
                BiasResponse(
                    variant_id=variant.id,
                    model_name=model_name,
                    response_text=response_text,
                    latency_ms=latency_ms,
                )
            )
            written += 1

            if (i + 1) % 10 == 0:
                logger.info("Progress: %d / %d variants", i + 1, len(variants))
                await session.flush()

    await session.flush()
    logger.info("Wrote %d new bias responses for language=%s", written, language)
    return written
