import asyncio
import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import httpx

NS = {"atom": "http://www.w3.org/2005/Atom"}
_BASE_URL = "http://export.arxiv.org/api/query"
_PAGE_SIZE = 100


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    categories: str


async def fetch_abstracts(client: httpx.AsyncClient, limit: int) -> list[ArxivPaper]:
    results: list[ArxivPaper] = []
    pages = math.ceil(limit / _PAGE_SIZE)

    for page in range(pages):
        start = page * _PAGE_SIZE
        max_results = min(_PAGE_SIZE, limit - len(results))
        params = {
            "search_query": "cat:cs.AI+OR+cat:cs.LG",
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
        response = await client.get(_BASE_URL, params=params)
        response.raise_for_status()

        root = ET.fromstring(response.text)
        for entry in root.findall("atom:entry", NS):
            raw_id = entry.find("atom:id", NS)
            title_el = entry.find("atom:title", NS)
            summary_el = entry.find("atom:summary", NS)
            if raw_id is None or title_el is None or summary_el is None:
                continue
            arxiv_id = raw_id.text.split("/abs/")[-1].strip()  # type: ignore[union-attr]
            categories = ",".join(c.get("term", "") for c in entry.findall("atom:category", NS))
            results.append(
                ArxivPaper(
                    arxiv_id=arxiv_id,
                    title=title_el.text.strip(),  # type: ignore[union-attr]
                    abstract=summary_el.text.strip(),  # type: ignore[union-attr]
                    categories=categories,
                )
            )

        if page < pages - 1:
            await asyncio.sleep(0.4)

    return results[:limit]
