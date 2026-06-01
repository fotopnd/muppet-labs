"""Generate 500+ synthetic cases from Jigsaw category patterns.

Usage:
    uv run python scripts/seed.py --confirm

Run with --confirm to truncate existing data and reseed.
"""
from __future__ import annotations

import argparse
import asyncio
import random
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.models import Base, Case, CaseCategory, CaseStatus, Severity

# Template sentences per category — enough variety to produce distinct-looking cases
TEMPLATES: dict[CaseCategory, list[str]] = {
    CaseCategory.toxic: [
        "You are absolutely worthless and nobody wants you here.",
        "Get out of this community, you disgusting excuse for a person.",
        "Stop posting your garbage opinions nobody asked for.",
        "I can't stand reading your idiotic takes on everything.",
        "People like you are the reason this platform is a cesspool.",
    ],
    CaseCategory.severe_toxic: [
        "I hope you get seriously hurt and never come back.",
        "You deserve everything bad that's coming to you, you waste of space.",
        "Kill yourself and do everyone a favour.",
        "Someone should find you and teach you a lesson you won't forget.",
        "You're a cancer on this community and should be permanently removed.",
    ],
    CaseCategory.obscene: [
        "That's the most f***ing stupid thing I've ever read.",
        "Holy s**t, how are you this dumb?",
        "What a complete piece of garbage argument.",
        "This post is pure bulls**t from start to finish.",
        "You can shove your opinion where the sun doesn't shine.",
    ],
    CaseCategory.threat: [
        "Watch your back because people know where you live.",
        "Keep posting like this and see what happens to you.",
        "I know who you are and I'm watching every move you make.",
        "One more comment like that and you'll regret it.",
        "You'd better delete this or you'll face consequences.",
    ],
    CaseCategory.insult: [
        "You are clearly the dumbest person on this platform.",
        "Did you fail every class in school? This is embarrassing.",
        "Congratulations on being the most ignorant commenter here.",
        "Your parents must be so ashamed of raising something like you.",
        "I've never seen someone so confidently wrong about everything.",
    ],
    CaseCategory.identity_hate: [
        "People from that country are all the same — dishonest and lazy.",
        "Of course someone like you would think that.",
        "Your kind has no business being in this discussion.",
        "This is exactly what's wrong with people of your background.",
        "Those people always stick together and cause trouble.",
    ],
}

SOURCES = ["web-forum", "mobile-app", "api-submission", "moderation-referral"]

# Severity weight by confidence score proxy: high = clear match, medium = moderate, low = borderline
SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.high: 0.3,
    Severity.medium: 0.45,
    Severity.low: 0.25,
}


def _make_case(category: CaseCategory, severity: Severity, idx: int) -> Case:
    template = TEMPLATES[category][idx % len(TEMPLATES[category])]
    # Add slight variation to avoid exact duplicates
    suffixes = ["", " Seriously.", " Do everyone a favour.", " Unbelievable.", " Just stop."]
    content = template + suffixes[idx % len(suffixes)]

    created_at = datetime.now(UTC) - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))

    return Case(
        id=str(uuid.uuid4()),
        content=content,
        category=category,
        severity=severity,
        status=CaseStatus.pending,
        source=random.choice(SOURCES),
        meta={"seed_index": idx, "confidence": round(0.5 + random.random() * 0.5, 3)},
        created_at=created_at,
        updated_at=created_at,
    )


def generate_cases(target: int = 540) -> list[Case]:
    """Generate at least `target` cases evenly distributed across 18 buckets (6 cat × 3 sev)."""
    categories = list(CaseCategory)
    severities = list(Severity)
    per_bucket = max(target // (len(categories) * len(severities)), 5)

    cases: list[Case] = []
    idx = 0
    for category in categories:
        for severity in severities:
            for _ in range(per_bucket):
                cases.append(_make_case(category, severity, idx))
                idx += 1
    return cases


async def main(confirm: bool) -> None:
    from app.config import settings

    if not confirm:
        print("Dry run — pass --confirm to actually seed the database.")
        cases = generate_cases()
        print(f"Would insert {len(cases)} cases across {len(CaseCategory)} categories × {len(Severity)} severities.")
        return

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE cases, decisions RESTART IDENTITY CASCADE"))
        print("Truncated existing data.")

    cases = generate_cases()
    async with session_factory() as session:
        session.add_all(cases)
        await session.commit()

    print(f"Seeded {len(cases)} cases.")
    await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the case-queue database.")
    parser.add_argument("--confirm", action="store_true", help="Actually run the seed (truncates first)")
    args = parser.parse_args()
    asyncio.run(main(args.confirm))
