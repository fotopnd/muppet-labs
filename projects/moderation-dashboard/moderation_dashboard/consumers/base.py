from __future__ import annotations

import logging
import signal
import time
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Literal

from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from moderation_dashboard.api.models import Classification
from moderation_dashboard.types import ModerationEvent

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    def __init__(
        self,
        model_name: str,
        group_id: str,
        mode: Literal["production", "shadow"],
        bootstrap_servers: str,
        topic: str,
        db_url: str,
    ) -> None:
        self.model_name = model_name
        self._group_id = group_id
        self._group = mode
        self._topic = topic
        self._running = True

        engine = create_engine(db_url)
        self._Session = sessionmaker(bind=engine)

        self._consumer = Consumer(
            {
                "bootstrap.servers": bootstrap_servers,
                "group.id": group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": False,
            }
        )

    @abstractmethod
    def classify(self, content: str) -> tuple[int, float]:
        """Return (predicted_label: 0|1, confidence: 0.0–1.0). Raise RuntimeError if weights not loaded."""
        raise NotImplementedError

    def _write_result(self, result: Classification) -> None:
        with self._Session() as session:
            session.add(result)
            session.commit()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._handle_sigint)
        self._consumer.subscribe([self._topic])
        processed = 0

        try:
            while self._running:
                msg = self._consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    raise KafkaException(msg.error())

                try:
                    event = ModerationEvent.model_validate_json(msg.value())
                    t0 = time.perf_counter()
                    predicted_label, confidence = self.classify(event.content)
                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    correct = predicted_label == event.ground_truth
                    group = self._group
                    result = Classification(
                        id=str(uuid.uuid4()),
                        event_id=event.event_id,
                        group=group,
                        model_name=self.model_name,
                        category=event.category,
                        content=event.content,
                        predicted_label=predicted_label,
                        confidence=confidence,
                        latency_ms=latency_ms,
                        correct=correct,
                        created_at=datetime.now(UTC),
                    )
                    self._write_result(result)
                    self._consumer.commit(asynchronous=False)
                    processed += 1
                    if processed % 100 == 0:
                        logger.debug(
                            "[%s/%s] processed=%d latency=%.1fms",
                            self.model_name,
                            self._group_id,
                            processed,
                            latency_ms,
                        )
                except Exception:
                    logger.warning(
                        "[%s/%s] Failed to process message",
                        self.model_name,
                        self._group_id,
                        exc_info=True,
                    )
        finally:
            self._consumer.close()
            logger.info(
                "[%s/%s] Consumer closed. Total processed: %d",
                self.model_name,
                self._group_id,
                processed,
            )

    def _handle_sigint(self, sig: int, frame: object) -> None:
        logger.info("[%s] Shutting down...", self.model_name)
        self._running = False
