"""ingest.py — POST /ingest webhook endpoint.

Accepts arbitrary text, publishes a ModerationEvent to Kafka, returns the event_id.
All active consumers pick up the event; no ground truth is available so correct=None.
"""
from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from confluent_kafka import Producer
from fastapi import APIRouter, HTTPException, Request

from moderation_dashboard.api.schemas import IngestRequest, IngestResponse
from moderation_dashboard.config import get_settings
from moderation_dashboard.types import ModerationEvent

router = APIRouter(tags=["ingest"])
logger = logging.getLogger(__name__)

# Module-level singleton — initialised on first request, shared across all requests.
_producer: Producer | None = None


def _get_producer() -> Producer:
    global _producer
    if _producer is None:
        settings = get_settings()
        _producer = Producer({"bootstrap.servers": settings.kafka_bootstrap_servers})
        logger.info("Ingest Kafka producer initialised at %s", settings.kafka_bootstrap_servers)
    return _producer


def _delivery_callback(err: Any, msg: Any) -> None:
    if err:
        logger.warning("Ingest delivery failed: %s", err)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest, request: Request) -> IngestResponse:
    text = body.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="text must not be empty")

    settings = get_settings()
    event_id = str(uuid.uuid4())
    event = ModerationEvent(
        event_id=event_id,
        jigsaw_id=-1,
        content=text,
        ground_truth=None,
        category="unknown",
        published_at=datetime.now(UTC),
    )

    producer = _get_producer()
    producer.produce(
        topic=settings.kafka_topic,
        value=event.model_dump_json().encode(),
        on_delivery=_delivery_callback,
    )
    # Non-blocking poll to process delivery reports without waiting for flush
    producer.poll(0)

    return IngestResponse(event_id=event_id)
