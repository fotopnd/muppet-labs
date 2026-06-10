"""
Outbox publisher — polls synthetic_events_outbox for unpublished rows and
injects them into the monitor's Kafka topic as LLMInteractionEvent JSON.

Run as a daemon:
    uv run outbox-publisher

The publisher marks each row published_at after successful Kafka delivery,
ensuring at-least-once delivery. Monitor consumers are idempotent
(UNIQUE constraint on event_id + model_name + classifier_version).
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

_POLL_INTERVAL_S = 5
_BATCH_SIZE = 100


def _build_kafka_message(row: dict) -> bytes:
    """Construct LLMInteractionEvent JSON matching the monitor's consumer contract."""
    payload = {
        "event_id": str(row["event_id"]),
        "prompt": row["prompt_text"],
        "response": row["response_text"],
        "source_dataset": "red_team",
        "ground_truth_safe": None,
        "ground_truth_categories": None,
    }
    return json.dumps(payload).encode()


def run_publisher() -> None:
    import psycopg2

    from confluent_kafka import Producer

    from red_team_platform.config import get_settings

    settings = get_settings()

    producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})

    conn = psycopg2.connect(str(settings.database_url).replace("+asyncpg", ""))
    conn.autocommit = False

    logger.info("Outbox publisher started. Polling every %ds.", _POLL_INTERVAL_S)

    while True:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, event_id, prompt_text, response_text,
                           jailbreak_success, classifier_score
                    FROM synthetic_events_outbox
                    WHERE published_at IS NULL
                    ORDER BY created_at
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED
                    """,
                    (_BATCH_SIZE,),
                )
                rows = cur.fetchall()

                if not rows:
                    conn.commit()
                    time.sleep(_POLL_INTERVAL_S)
                    continue

                published_ids = []
                for row in rows:
                    row_id, event_id, prompt, response, jailbreak, score = row
                    msg = _build_kafka_message(
                        {
                            "event_id": event_id,
                            "prompt_text": prompt,
                            "response_text": response,
                        }
                    )
                    producer.produce(
                        settings.kafka_topic,
                        value=msg,
                        key=str(event_id).encode(),
                    )
                    published_ids.append(row_id)

                producer.flush()

                cur.execute(
                    """
                    UPDATE synthetic_events_outbox
                    SET published_at = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (datetime.now(UTC), [str(i) for i in published_ids]),
                )
                conn.commit()
                logger.info("Published %d events from outbox.", len(published_ids))

        except Exception as exc:
            logger.error("Publisher error: %s", exc, exc_info=True)
            try:
                conn.rollback()
            except Exception:
                pass
            time.sleep(_POLL_INTERVAL_S)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    run_publisher()
