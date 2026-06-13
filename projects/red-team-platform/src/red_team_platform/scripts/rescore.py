"""
Re-score all existing runs using the LLM judge (claude-haiku-4-5-20251001).

Replaces the broken constant PAIR classifier scores (0.025 / 0.505) with
continuous scores from the haiku judge. Updates classifier_score and
jailbreak_success in place. Recomputes session ASR after all runs are updated.
Refreshes coverage_summary materialised view.

Usage:
    uv run rescore
    uv run rescore --session-id <uuid>   # re-score a single session
    uv run rescore --dry-run             # print scores, don't update
"""
from __future__ import annotations

import asyncio
import logging
import uuid as uuid_mod

import typer
from sqlalchemy import select, update
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

app = typer.Typer()


@app.command()
def main(
    session_id: Annotated[str | None, typer.Option("--session-id")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    limit: Annotated[int | None, typer.Option("--limit", help="Cap number of runs (useful with --dry-run)")] = None,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory
    from red_team_platform.models import Attack, Run, RunSession
    from red_team_platform.runner.judge import judge

    settings = get_settings()

    target_session_id: uuid_mod.UUID | None = None
    if session_id:
        try:
            target_session_id = uuid_mod.UUID(session_id)
        except ValueError:
            raise typer.BadParameter(f"Invalid UUID: {session_id!r}")

    async def _run() -> None:
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)

        # Load runs with their attack text
        async with factory() as session:
            stmt = (
                select(
                    Run.id,
                    Run.session_id,
                    Run.response_text,
                    Attack.attack_text,
                )
                .join(Attack, Run.attack_id == Attack.id)
            )
            if target_session_id:
                stmt = stmt.where(Run.session_id == target_session_id)
            result = await session.execute(stmt)
            runs = result.all()

        if limit:
            runs = runs[:limit]
        logger.info("Loaded %d runs to re-score", len(runs))

        # Re-score all runs with bounded concurrency (10 parallel haiku calls)
        semaphore = asyncio.Semaphore(10)
        updated_runs: list[tuple[uuid_mod.UUID, bool, float]] = []
        completed = 0

        async def score_one(run):
            nonlocal completed
            async with semaphore:
                success, score = await judge(run.attack_text, run.response_text)
                completed += 1
                if completed % 100 == 0:
                    logger.info("Re-scored %d / %d runs", completed, len(runs))
                return run.id, run.session_id, success, score

        results = await asyncio.gather(*[score_one(r) for r in runs])
        updated_runs = [(run_id, success, score) for run_id, _, success, score in results]

        if dry_run:
            for run_id, _, success, score in results[:10]:
                print(f"run {run_id}: score={score:.3f} success={success}")

        if dry_run:
            successes = sum(1 for _, s, _ in updated_runs if s)
            print(f"\nDry run: would update {len(runs)} runs. "
                  f"New success rate: {successes}/{len(runs)} = {successes/len(runs):.1%}")
            await engine.dispose()
            return

        # Batch update runs
        async with factory() as session:
            for run_id, success, score in updated_runs:
                await session.execute(
                    update(Run)
                    .where(Run.id == run_id)
                    .values(classifier_score=score, jailbreak_success=success)
                )
            await session.commit()

        logger.info("Updated %d runs", len(updated_runs))

        # Recompute session ASR for affected sessions
        affected_session_ids = {sid for _, sid, _, _ in results}
        async with factory() as session:
            for sid in affected_session_ids:
                result = await session.execute(
                    select(Run.jailbreak_success).where(Run.session_id == sid)
                )
                successes_rows = result.scalars().all()
                total = len(successes_rows)
                successes = sum(1 for s in successes_rows if s)
                asr = successes / total if total > 0 else 0.0
                await session.execute(
                    update(RunSession)
                    .where(RunSession.id == sid)
                    .values(total_attacks=total, total_successes=successes, asr=asr)
                )
            await session.commit()

        logger.info("Recomputed ASR for %d sessions", len(affected_session_ids))

        # Refresh materialised view
        from sqlalchemy import text
        async with factory() as session:
            await session.execute(text("REFRESH MATERIALIZED VIEW coverage_summary"))
            await session.commit()

        await engine.dispose()
        print(f"\nRe-scored {len(updated_runs)} runs across {len(affected_session_ids)} sessions.")
        print("Run: SELECT stddev(classifier_score) FROM runs; -- should be > 0.1")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
