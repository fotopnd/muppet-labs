"""demo_stream.py — POST synthetic events to /ingest at a configurable rate.

Loads a sample of Jigsaw rows at startup and cycles through them, sending each
comment_text as a live webhook event. Keeps the StreamMonitor animating without
needing the CSV producer running.

Usage:
    uv run demo-stream                 # 3 events/sec, 200-row sample
    uv run demo-stream --rate 10       # 10 events/sec
    uv run demo-stream --rate 1 --sample 50
    uv run demo-stream --api http://localhost:8002
"""
from __future__ import annotations

import argparse
import csv
import itertools
import logging
import random
import signal
import time
from pathlib import Path

import httpx

from moderation_dashboard.config import get_settings

logger = logging.getLogger(__name__)

_running = True


def _handle_sigint(sig: int, frame: object) -> None:
    global _running
    logger.info("Shutting down demo stream...")
    _running = False


def load_sample(csv_path: Path, n: int) -> list[str]:
    texts: list[str] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = row.get("comment_text", "").strip()
            if text:
                texts.append(text)
    if len(texts) > n:
        texts = random.sample(texts, n)
    logger.info("Loaded %d sample texts from %s", len(texts), csv_path)
    return texts


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Stream synthetic events to /ingest")
    parser.add_argument("--rate", type=float, default=3.0, help="Events per second (default: 3)")
    parser.add_argument("--sample", type=int, default=200, help="Rows to sample from CSV (default: 200)")
    parser.add_argument("--api", type=str, default="http://localhost:8002", help="API base URL")
    args = parser.parse_args()

    settings = get_settings()
    csv_path = Path(settings.jigsaw_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Jigsaw CSV not found at {csv_path}")

    texts = load_sample(csv_path, args.sample)
    interval = 1.0 / args.rate
    url = f"{args.api.rstrip('/')}/ingest"

    signal.signal(signal.SIGINT, _handle_sigint)
    logger.info("Streaming to %s at %.1f events/sec — Ctrl-C to stop", url, args.rate)

    sent = 0
    with httpx.Client(timeout=5.0) as client:
        for text in itertools.cycle(texts):
            if not _running:
                break
            t0 = time.monotonic()
            try:
                resp = client.post(url, json={"text": text})
                resp.raise_for_status()
                sent += 1
                if sent % 50 == 0:
                    logger.info("Sent %d events", sent)
            except Exception:
                logger.warning("POST /ingest failed", exc_info=True)

            elapsed = time.monotonic() - t0
            wait = interval - elapsed
            if wait > 0:
                time.sleep(wait)

    logger.info("Demo stream stopped. Total sent: %d", sent)


if __name__ == "__main__":
    main()
