"""Generate document_library cards via Ollama.

This script is written but NOT run during the MVP build.
Run after seed data has been verified and the full Ollama-backed generation is ready.

Usage:
    uv run generate-library --n-cards 300 --model gemma2:9b --phase 1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

import httpx

from year_zero.config import settings
from year_zero.database import engine, init_db, session_factory
from year_zero.models import DocumentLibrary

HARM_CATEGORIES = [
    "violence",
    "hate_speech",
    "pii_exposure",
    "cybercrime",
    "sexual_content",
    "misinformation",
    "child_safety",
    "self_harm",
    "weapons",
    "extremism",
    "privacy",
    "fraud",
    "harassment",
]

GENERATION_PROMPT_TEMPLATE = """
You are generating documents for a Cold War bureaucratic registry game.
Generate a {harm_category} document in the style of Soviet-era official correspondence.
The document should be {harmful_label} and use the {strategy} obfuscation technique.
Format the response as JSON with keys: prompt_text, document_text, sovereign_verdict (bool or null),
sovereign_confidence (0.0-1.0), sovereign_reasoning (str).
Document text should be 2-4 sentences of Cold War bureaucratic prose.
"""


async def generate_card(
    client: httpx.AsyncClient,
    model: str,
    harm_category: str,
    is_harmful: bool,
    strategy: str,
    phase: int,
    generation_tier: int,
) -> dict | None:
    prompt = GENERATION_PROMPT_TEMPLATE.format(
        harm_category=harm_category,
        harmful_label="harmful" if is_harmful else "benign",
        strategy=strategy,
    )
    try:
        resp = await client.post(
            f"{settings.ollama_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False, "format": "json"},
            timeout=60.0,
        )
        resp.raise_for_status()
        data = resp.json()
        card_data = json.loads(data["response"])
        return {
            "prompt_text": card_data["prompt_text"],
            "document_text": card_data["document_text"],
            "generation_model": model,
            "generation_tier": generation_tier,
            "strategy": strategy,
            "harm_category": harm_category,
            "is_harmful": is_harmful,
            "phase": phase,
            "sovereign_verdict": card_data.get("sovereign_verdict"),
            "sovereign_confidence": card_data.get("sovereign_confidence"),
            "sovereign_reasoning": card_data.get("sovereign_reasoning"),
            "verdict_correct": (
                None
                if card_data.get("sovereign_verdict") is None
                else (card_data["sovereign_verdict"] == is_harmful)
            ),
            "target_condition_mix": {"none": 0.25, "tier_1": 0.25, "tier_2": 0.25, "tier_3": 0.25},
        }
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as exc:
        print(f"  WARN: skipping card — {exc}", file=sys.stderr)
        return None


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate document library cards via Ollama")
    parser.add_argument("--n-cards", type=int, default=100, help="Number of cards to generate")
    parser.add_argument("--model", type=str, default="gemma2:9b", help="Ollama model name")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3], default=1, help="Game phase")
    args = parser.parse_args()

    tier_map = {"gemma2:9b": 1, "qwen2.5:7b": 2, "llama3.1:8b": 3}
    generation_tier = tier_map.get(args.model, 1)

    strategies = ["AIM", "prefix_injection", "refusal_suppression", "base64", "direct_request"]

    await init_db()

    cards_written = 0
    async with httpx.AsyncClient() as client:
        async with session_factory() as db:
            for i in range(args.n_cards):
                harm_category = HARM_CATEGORIES[i % len(HARM_CATEGORIES)]
                strategy = strategies[i % len(strategies)]
                is_harmful = (i % 2) == 0

                card = await generate_card(
                    client,
                    args.model,
                    harm_category,
                    is_harmful,
                    strategy,
                    args.phase,
                    generation_tier,
                )
                if card is None:
                    continue

                db.add(DocumentLibrary(**card))
                if (i + 1) % 10 == 0:
                    await db.commit()
                    print(f"  {i + 1}/{args.n_cards} cards committed")
                cards_written += 1

            await db.commit()

    print(f"Done. {cards_written} cards written.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
