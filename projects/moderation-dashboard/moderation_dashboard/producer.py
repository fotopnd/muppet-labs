from __future__ import annotations

import argparse
import csv
import logging
import signal
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from moderation_dashboard.config import get_settings
from moderation_dashboard.types import ModerationEvent

logger = logging.getLogger(__name__)

CATEGORY_PRIORITY: list[str] = [
    "severe_toxic",
    "threat",
    "identity_hate",
    "obscene",
    "insult",
    "toxic",
]


def get_primary_category(row: dict[str, Any]) -> str:
    for cat in CATEGORY_PRIORITY:
        if cat in row and int(float(row[cat])) == 1:
            return cat
    return "clean"


def load_jigsaw_csv(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if limit is not None and idx >= limit:
                break
            content = row.get("comment_text", "").strip()
            if not content:
                continue
            rows.append({**row, "_idx": idx})
    return rows


def ensure_topic(bootstrap_servers: str, topic: str, num_partitions: int) -> None:
    admin = AdminClient({"bootstrap.servers": bootstrap_servers})
    # Retry — librdkafka sometimes resets the first connection attempt
    metadata = None
    for attempt in range(6):
        try:
            metadata = admin.list_topics(timeout=5)
            if metadata.topics:
                break
        except Exception:
            pass
        logger.info("Waiting for Kafka metadata (attempt %d/6)...", attempt + 1)
        time.sleep(3)
    if metadata is None:
        raise RuntimeError(f"Could not connect to Kafka at {bootstrap_servers} after 6 attempts")
    if topic not in metadata.topics:
        new_topic = NewTopic(topic, num_partitions=num_partitions, replication_factor=1)
        futures = admin.create_topics([new_topic])
        for _t, future in futures.items():
            try:
                future.result()
                logger.info("Created topic '%s' with %d partitions", topic, num_partitions)
            except Exception as exc:
                if "already exists" not in str(exc).lower():
                    raise


def publish_events(
    events: list[dict[str, Any]],
    bootstrap_servers: str,
    topic: str,
    rate_per_sec: float,
) -> None:
    producer = Producer({"bootstrap.servers": bootstrap_servers})
    running = True

    def _sigint(sig: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _sigint)

    interval = 1.0 / max(rate_per_sec, 1)
    start = time.monotonic()
    total = 0

    for raw in events:
        if not running:
            break
        event = ModerationEvent(
            event_id=str(uuid.uuid4()),
            jigsaw_id=raw["_idx"],
            content=raw["comment_text"].strip(),
            ground_truth=int(float(raw.get("toxic", 0))),
            category=get_primary_category(raw),
            published_at=datetime.now(UTC),
        )
        producer.produce(topic, key=event.event_id, value=event.model_dump_json())
        producer.poll(0)
        total += 1
        if total % 500 == 0:
            logger.info("Published %d events", total)
        elapsed = time.monotonic() - start
        expected = total * interval
        if expected > elapsed:
            time.sleep(expected - elapsed)

    producer.flush()
    logger.info("Done. Published %d events.", total)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Jigsaw Kafka producer for moderation-dashboard")
    parser.add_argument("--limit", type=int, default=1000, help="Max messages (0 = all rows)")
    args = parser.parse_args()

    settings = get_settings()
    limit: int | None = args.limit if args.limit > 0 else None

    try:
        logger.info(
            "Ensuring topic '%s' exists (%d partitions)...",
            settings.kafka_topic,
            settings.kafka_num_partitions,
        )
        ensure_topic(
            settings.kafka_bootstrap_servers, settings.kafka_topic, settings.kafka_num_partitions
        )
    except Exception:
        # Topic is auto-created by KAFKA_CREATE_TOPICS; AdminClient transport errors are non-fatal
        logger.warning("ensure_topic failed — proceeding anyway", exc_info=True)

    logger.info("Loading events from %s (limit=%s)...", settings.jigsaw_csv_path, limit or "all")
    events = load_jigsaw_csv(settings.jigsaw_csv_path, limit)
    logger.info(
        "Loaded %d events. Publishing at %.1f msg/sec...",
        len(events),
        settings.producer_rate_per_sec,
    )
    publish_events(
        events,
        settings.kafka_bootstrap_servers,
        settings.kafka_topic,
        settings.producer_rate_per_sec,
    )
