from __future__ import annotations

import argparse
import csv
import logging
import signal
import time
import uuid
from collections.abc import Iterator
from pathlib import Path

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

from moderation_stream.config import Settings
from moderation_stream.types import ModerationEvent

logger = logging.getLogger(__name__)


def create_producer(bootstrap_servers: str) -> Producer:
    return Producer({"bootstrap.servers": bootstrap_servers})


def ensure_topic(bootstrap_servers: str, topic: str) -> None:
    admin = AdminClient({"bootstrap.servers": bootstrap_servers})
    metadata = admin.list_topics(timeout=5)
    if topic not in metadata.topics:
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        futures = admin.create_topics([new_topic])
        for _t, future in futures.items():
            try:
                future.result()
            except Exception as exc:
                if "already exists" not in str(exc).lower():
                    raise


def load_jigsaw_csv(csv_path: Path, limit: int | None) -> Iterator[ModerationEvent]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if limit is not None and count >= limit:
                break
            text = row.get("comment_text", "").strip()
            if not text:
                continue
            category_keys = ("toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate")
            label_detail = {k: float(row[k]) for k in category_keys if k in row}
            label = int(float(row["toxic"])) if "toxic" in row else None
            yield ModerationEvent(
                event_id=str(uuid.uuid4()),
                text=text,
                label=label,
                label_detail=label_detail if label_detail else None,
            )
            count += 1


def publish_events(
    producer: Producer,
    events: Iterator[ModerationEvent],
    topic: str,
    rate_per_sec: int,
) -> int:
    running = True

    def _sigint(sig: int, frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _sigint)

    total = 0
    interval = 1.0 / max(rate_per_sec, 1)
    start = time.monotonic()

    for event in events:
        if not running:
            break
        producer.produce(topic, key=event.event_id, value=event.model_dump_json())
        producer.poll(0)
        total += 1
        elapsed = time.monotonic() - start
        expected = total * interval
        if expected > elapsed:
            time.sleep(expected - elapsed)

    producer.flush()
    return total


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Jigsaw dataset Kafka producer")
    parser.add_argument("--limit", type=int, default=1000, help="Max messages (0 = all rows)")
    args = parser.parse_args()

    settings = Settings()
    limit: int | None = args.limit if args.limit > 0 else None

    logger.info("Ensuring topic '%s' exists...", settings.kafka_topic)
    ensure_topic(settings.kafka_bootstrap_servers, settings.kafka_topic)

    logger.info("Loading events from %s (limit=%s)...", settings.jigsaw_csv_path, limit or "all")
    events = load_jigsaw_csv(settings.jigsaw_csv_path, limit)
    producer = create_producer(settings.kafka_bootstrap_servers)

    logger.info("Publishing at %d msg/sec...", settings.producer_rate_per_sec)
    start = time.monotonic()
    total = publish_events(producer, events, settings.kafka_topic, settings.producer_rate_per_sec)
    elapsed = time.monotonic() - start

    logger.info("Done. Published %d events in %.1fs (%.1f msg/sec)", total, elapsed, total / elapsed)
