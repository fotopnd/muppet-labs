import asyncio

import httpx
from sqlalchemy import select

from error_hide_seek.config import settings
from error_hide_seek.corpus.arxiv import fetch_abstracts
from error_hide_seek.db import AsyncSessionLocal, init_db
from error_hide_seek.models import Paper


async def _run() -> None:
    await init_db()
    async with httpx.AsyncClient(timeout=30.0) as client:
        papers = await fetch_abstracts(client, settings.corpus_size)

    fetched = len(papers)
    skipped = 0

    async with AsyncSessionLocal() as session:
        for paper in papers:
            existing = await session.scalar(select(Paper).where(Paper.arxiv_id == paper.arxiv_id))
            if existing is not None:
                skipped += 1
                continue
            session.add(
                Paper(
                    arxiv_id=paper.arxiv_id,
                    title=paper.title,
                    abstract=paper.abstract,
                    categories=paper.categories,
                )
            )
        await session.commit()

    inserted = fetched - skipped
    print(f"Fetched {fetched}, inserted {inserted}, skipped {skipped} (already present).")


def main() -> None:
    asyncio.run(_run())
