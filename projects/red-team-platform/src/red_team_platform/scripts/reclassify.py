"""
Batch-reclassify attacks.harm_category using claude-haiku-4-5-20251001.

Processes all 10,800 attacks in batches of 50. For each batch, sends attack_text
to haiku and asks it to assign one of 13 WildGuard-compatible categories.
Updates harm_category in place — no schema changes.

Usage:
    uv run reclassify
    uv run reclassify --batch-size 25
    uv run reclassify --dry-run --limit 10
"""
from __future__ import annotations

import asyncio
import json
import logging
import sys

import typer
from sqlalchemy import select, update
from typing_extensions import Annotated

logger = logging.getLogger(__name__)

WILDGUARD_CATEGORIES = [
    "cybercrime_and_intrusion",
    "harmful_information_generation",
    "hate_and_discrimination",
    "human_trafficking",
    "illegal_activities",
    "intellectual_property",
    "misinformation",
    "physical_harm",
    "privacy_violation",
    "psychological_manipulation",
    "self_harm",
    "sexual_content",
    "violence",
]

_CATEGORY_LIST = ", ".join(WILDGUARD_CATEGORIES)

_BATCH_PROMPT = """You are a content safety classifier. For each numbered text below, assign exactly one harm category.

Categories: {categories}

Texts:
{texts}

Respond with a JSON array of exactly {n} strings, one category per text in order.
Use only categories from the list above. Example: ["violence", "sexual_content"]"""


async def classify_batch(
    client,  # anthropic.AsyncAnthropic
    texts: list[str],
) -> list[str]:
    numbered = "\n".join(f"{i + 1}. {t[:500]}" for i, t in enumerate(texts))
    prompt = _BATCH_PROMPT.format(
        categories=_CATEGORY_LIST,
        texts=numbered,
        n=len(texts),
    )
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = (message.content[0].text or "").strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        categories = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JSON parse failed for batch, falling back per-item: %r", raw[:200])
        return ["illegal_activities"] * len(texts)

    if not isinstance(categories, list) or len(categories) != len(texts):
        logger.warning(
            "Unexpected category count: got %d, expected %d",
            len(categories) if isinstance(categories, list) else -1,
            len(texts),
        )
        return ["illegal_activities"] * len(texts)

    # Normalise: ensure each value is a known category
    validated = []
    for cat in categories:
        c = str(cat).strip().lower()
        if c not in WILDGUARD_CATEGORIES:
            logger.warning("Unknown category %r — using 'illegal_activities'", c)
            c = "illegal_activities"
        validated.append(c)
    return validated


app = typer.Typer()


@app.command()
def main(
    batch_size: Annotated[int, typer.Option("--batch-size")] = 50,
    dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    limit: Annotated[int | None, typer.Option("--limit", help="Cap number of attacks (useful with --dry-run)")] = None,
) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

    if dry_run and limit is None:
        raise typer.BadParameter("--dry-run requires --limit N (e.g. --dry-run --limit 10)")

    import anthropic

    from red_team_platform.config import get_settings
    from red_team_platform.db import create_engine, create_session_factory
    from red_team_platform.models import Attack

    settings = get_settings()

    async def _run() -> None:
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key or None)
        engine = create_engine(settings.database_url)
        factory = create_session_factory(engine)

        async with factory() as session:
            result = await session.execute(select(Attack.id, Attack.attack_text))
            rows = result.all()

        if limit:
            rows = rows[:limit]
        logger.info("Loaded %d attacks to reclassify", len(rows))

        total_updated = 0
        for batch_start in range(0, len(rows), batch_size):
            batch = rows[batch_start : batch_start + batch_size]
            ids = [r.id for r in batch]
            texts = [r.attack_text for r in batch]

            categories = await classify_batch(client, texts)

            if dry_run:
                for i, (attack_id, cat) in enumerate(zip(ids, categories)):
                    print(f"{attack_id}: {cat}")
            else:
                async with factory() as session:
                    for attack_id, cat in zip(ids, categories):
                        await session.execute(
                            update(Attack)
                            .where(Attack.id == attack_id)
                            .values(harm_category=cat)
                        )
                    await session.commit()

            total_updated += len(batch)
            logger.info(
                "Progress: %d / %d attacks reclassified",
                total_updated,
                len(rows),
            )

        await engine.dispose()

        if dry_run:
            print(f"\nDry run complete — would have updated {len(rows)} attacks.")
        else:
            print(f"\nReclassified {total_updated} attacks.")
            print("Run: SELECT harm_category, COUNT(*) FROM attacks GROUP BY harm_category ORDER BY COUNT(*) DESC;")

    asyncio.run(_run())


if __name__ == "__main__":
    app()
