"""bsky_stream.py — Feed the moderation pipeline from the live Bluesky firehose.

Subscribes to Bluesky's Jetstream websocket, which emits every public post on the
network in real time. Filters for English-language text posts, rate-limits to keep
local MPS inference from backing up, and POSTs each post's text to the same /ingest
webhook used by demo_stream.py — so Kafka, the consumers, shadow comparison, anomaly
detection, and the dashboard all see *real* content with no further changes.

There is no ground truth on live posts (correct=NULL), so the live cards show
throughput, latency, toxic/clean distribution, and model disagreement — accuracy
itself is reported separately on the held-out Jigsaw test set.

Usage:
    uv run bsky-stream                      # ~5 posts/sec to localhost:8002
    uv run bsky-stream --rate 10            # cap at 10 posts/sec
    uv run bsky-stream --api http://my-vps  # target a deployed API
    uv run bsky-stream --no-lang-filter     # accept all languages
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import signal
import time

import httpx
import websockets

logger = logging.getLogger(__name__)

# Jetstream public endpoint — no auth required. Filtered server-side to feed posts.
JETSTREAM_URL = (
    "wss://jetstream2.us-east.bsky.network/subscribe"
    "?wantedCollections=app.bsky.feed.post"
)

_running = True


def _handle_sigint(sig: int, frame: object) -> None:
    global _running
    logger.info("Shutting down Bluesky stream...")
    _running = False


def _extract_post_text(event: dict, lang_filter: bool) -> str | None:
    """Pull post text from a Jetstream commit event, or None if it should be skipped."""
    if event.get("kind") != "commit":
        return None
    commit = event.get("commit") or {}
    if commit.get("operation") != "create":
        return None
    if commit.get("collection") != "app.bsky.feed.post":
        return None

    record = commit.get("record") or {}
    text = (record.get("text") or "").strip()
    if not text:
        return None

    if lang_filter:
        langs = record.get("langs")
        # Accept when 'en' is declared; if langs is absent, accept best-effort.
        if langs and "en" not in langs:
            return None

    return text


async def _post(client: httpx.AsyncClient, url: str, text: str) -> bool:
    try:
        resp = await client.post(url, json={"text": text})
        resp.raise_for_status()
        return True
    except Exception:
        logger.warning("POST /ingest failed", exc_info=True)
        return False


async def _stream(url: str, rate: float, lang_filter: bool) -> None:
    interval = 1.0 / rate
    next_send = time.monotonic()
    sent = 0
    seen = 0
    backoff = 1.0

    async with httpx.AsyncClient(timeout=5.0) as client:
        while _running:
            try:
                async with websockets.connect(
                    JETSTREAM_URL, ping_interval=20, ping_timeout=20, max_size=None
                ) as ws:
                    logger.info("Connected to Jetstream — streaming live posts to %s", url)
                    backoff = 1.0  # reset on a successful connect
                    async for raw in ws:
                        if not _running:
                            break
                        seen += 1
                        try:
                            event = json.loads(raw)
                        except (ValueError, TypeError):
                            continue

                        text = _extract_post_text(event, lang_filter)
                        if text is None:
                            continue

                        # Rate cap: drop (sample) posts arriving faster than the target rate
                        now = time.monotonic()
                        if now < next_send:
                            continue
                        next_send = now + interval

                        if await _post(client, url, text):
                            sent += 1
                            if sent % 50 == 0:
                                logger.info(
                                    "Sent %d posts (%d firehose events seen)", sent, seen
                                )
            except (websockets.ConnectionClosed, OSError) as exc:
                if not _running:
                    break
                logger.warning("Jetstream connection dropped (%s) — reconnecting in %.0fs", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

    logger.info("Bluesky stream stopped. Total posts sent: %d", sent)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Stream live Bluesky posts to /ingest")
    parser.add_argument("--rate", type=float, default=5.0, help="Max posts per second (default: 5)")
    parser.add_argument("--api", type=str, default="http://localhost:8002", help="API base URL")
    parser.add_argument(
        "--no-lang-filter",
        action="store_true",
        help="Accept all languages (default: English-only, matching the classifier)",
    )
    args = parser.parse_args()

    url = f"{args.api.rstrip('/')}/ingest"
    signal.signal(signal.SIGINT, _handle_sigint)
    logger.info("Streaming Bluesky firehose to %s at up to %.1f posts/sec — Ctrl-C to stop", url, args.rate)

    try:
        asyncio.run(_stream(url, args.rate, lang_filter=not args.no_lang_filter))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
