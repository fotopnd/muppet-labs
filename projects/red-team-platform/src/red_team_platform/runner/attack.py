from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Annotated

import typer
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from red_team_platform.models import Attack, Run, RunSession
from red_team_platform.runner.classifier import score, warm_up
from red_team_platform.runner.ollama_client import chat, make_client

logger = logging.getLogger(__name__)

app = typer.Typer()


async def run_session(
    session: AsyncSession,
    model_name: str,
    source_filter: str | None,
    harm_category_filter: str | None,
    strategy_filter: str | None,
    ollama_base_url: str,
    ollama_model: str,
    ollama_timeout_s: int,
) -> uuid.UUID:
    """
    Creates a RunSession row, iterates over filtered attacks, fires each at Ollama,
    scores with pair_classifier, writes Run rows, closes session with aggregate stats,
    refreshes coverage_summary materialised view.
    Returns the session UUID.
    """
    # Build attack query
    stmt = select(Attack)
    if source_filter:
        stmt = stmt.where(Attack.source == source_filter)
    if harm_category_filter:
        stmt = stmt.where(Attack.harm_category == harm_category_filter)
    if strategy_filter:
        stmt = stmt.where(Attack.strategy == strategy_filter)

    result = await session.execute(stmt)
    attacks = result.scalars().all()

    if not attacks:
        logger.warning("No attacks found matching filters. Exiting.")
        raise SystemExit(1)

    logger.info("Found %d attacks to run", len(attacks))

    # Create run session
    run_session_obj = RunSession(model_name=model_name)
    session.add(run_session_obj)
    await session.flush()
    session_id = run_session_obj.id

    total_attacks = 0
    total_successes = 0

    async with make_client(ollama_base_url, ollama_timeout_s) as client:
        for i, attack in enumerate(attacks):
            try:
                response_text, latency_ms = await chat(client, ollama_model, attack.attack_text)
            except Exception as exc:
                logger.warning(
                    "Attack %s timed out or failed: %s",
                    attack.id,
                    exc,
                    exc_info=True,
                )
                continue

            jailbreak_success, classifier_score = score(attack.attack_text, response_text)

            run = Run(
                session_id=session_id,
                attack_id=attack.id,
                model_name=model_name,
                response_text=response_text,
                jailbreak_success=jailbreak_success,
                classifier_score=classifier_score,
                latency_ms=latency_ms,
            )
            session.add(run)
            await session.flush()  # get run.id before outbox write

            # Outbox row is written atomically with the Run row so the publisher
            # only sees results that are fully committed.
            await session.execute(
                text("""
                    INSERT INTO synthetic_events_outbox
                        (run_id, prompt_text, response_text, jailbreak_success, classifier_score)
                    VALUES (:run_id, :prompt, :response, :jailbreak, :score)
                """),
                {
                    "run_id": run.id,
                    "prompt": attack.attack_text,
                    "response": response_text,
                    "jailbreak": jailbreak_success,
                    "score": classifier_score,
                },
            )

            total_attacks += 1
            if jailbreak_success:
                total_successes += 1

            if (i + 1) % 10 == 0:
                logger.info(
                    "Progress: %d / %d attacks | successes: %d",
                    i + 1,
                    len(attacks),
                    total_successes,
                )
                await session.flush()

    # Update session stats
    asr = total_successes / total_attacks if total_attacks > 0 else 0.0
    await session.execute(
        update(RunSession)
        .where(RunSession.id == session_id)
        .values(total_attacks=total_attacks, total_successes=total_successes, asr=asr)
    )
    await session.commit()

    # Refresh coverage materialised view
    await session.execute(text("REFRESH MATERIALIZED VIEW coverage_summary"))
    await session.commit()

    logger.info(
        "Session %s complete. Attacks: %d, Successes: %d, ASR: %.3f",
        session_id,
        total_attacks,
        total_successes,
        asr,
    )
    return session_id


_BIAS_LANGUAGES = frozenset({"en", "zh", "ru", "ar"})


@app.command()
def main(
    source: Annotated[str | None, typer.Option("--source")] = None,
    harm_category: Annotated[str | None, typer.Option("--harm-category")] = None,
    strategy: Annotated[str | None, typer.Option("--strategy")] = None,
    mode: Annotated[str, typer.Option("--mode", help="'normal' or 'bias'")] = "normal",
    language: Annotated[
        str | None,
        typer.Option("--language", help="Language for bias mode: en|zh|ru|ar"),
    ] = None,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory

    settings = get_settings()

    if mode not in ("normal", "bias"):
        raise typer.BadParameter(f"--mode must be 'normal' or 'bias', got {mode!r}")

    if mode == "bias":
        if language is None:
            raise typer.BadParameter("--language is required when --mode bias")
        if language not in _BIAS_LANGUAGES:
            raise typer.BadParameter(
                f"--language must be one of {sorted(_BIAS_LANGUAGES)}, got {language!r}"
            )

    if settings.ollama_model != "gemma2:9b":
        raise SystemExit(
            f"Preflight failed: ollama_model is '{settings.ollama_model}', expected 'gemma2:9b'. "
            "Set OLLAMA_MODEL=gemma2:9b in .env or override with the environment variable."
        )

    if mode == "bias":
        from red_team_platform.bias.runner import run_bias_session

        async def _run_bias() -> None:
            engine = create_engine(settings.database_url)
            factory = create_session_factory(engine)
            async with factory() as db_session:
                written = await run_bias_session(
                    session=db_session,
                    language=language,  # type: ignore[arg-type]
                    model_name=settings.ollama_model,
                    ollama_base_url=settings.ollama_base_url,
                    ollama_timeout_s=settings.ollama_timeout_s,
                )
                await db_session.commit()
            await engine.dispose()
            print(f"Wrote {written} new bias responses for language={language}.")

        asyncio.run(_run_bias())
        return

    warm_up(settings.pair_classifier_path)

    async def _run() -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)
        async with factory() as db_session:
            await run_session(
                session=db_session,
                model_name=settings.ollama_model,
                source_filter=source,
                harm_category_filter=harm_category,
                strategy_filter=strategy,
                ollama_base_url=settings.ollama_base_url,
                ollama_model=settings.ollama_model,
                ollama_timeout_s=settings.ollama_timeout_s,
            )
        await engine.dispose()

    asyncio.run(_run())
