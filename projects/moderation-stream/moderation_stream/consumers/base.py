from __future__ import annotations

import logging
import signal
import time
from abc import ABC, abstractmethod
from datetime import UTC, datetime

from confluent_kafka import Consumer, KafkaError, KafkaException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from moderation_stream.api.models import ClassificationResult
from moderation_stream.config import Settings
from moderation_stream.types import ModerationEvent

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    model_name: str
    consumer_group_id: str

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._running = True

        engine = create_engine(settings.database_url)
        self._Session = sessionmaker(bind=engine)

        self._consumer = Consumer({
            "bootstrap.servers": settings.kafka_bootstrap_servers,
            "group.id": self.consumer_group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })

        logger.info("Loading model %s...", self.model_name)
        self._load_model()
        logger.info("Model %s ready.", self.model_name)

    @abstractmethod
    def _load_model(self) -> None:
        """Load model weights into memory. Called once during __init__."""

    @abstractmethod
    def _run_inference(self, text: str) -> int:
        """Return predicted_label: 0 (not toxic) or 1 (toxic)."""

    def classify(self, text: str) -> tuple[int, float]:
        start = time.perf_counter()
        label = self._run_inference(text)
        latency_ms = (time.perf_counter() - start) * 1000.0
        return label, latency_ms

    def _write_result(self, result: ClassificationResult) -> None:
        with self._Session() as session:
            session.add(result)
            session.commit()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self._handle_sigint)
        self._consumer.subscribe([self._settings.kafka_topic])
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
                    predicted_label, latency_ms = self.classify(event.text)
                    correct = (predicted_label == event.label) if event.label is not None else None
                    result = ClassificationResult(
                        event_id=event.event_id,
                        model_name=self.model_name,
                        predicted_label=predicted_label,
                        latency_ms=latency_ms,
                        correct=correct,
                        processed_at=datetime.now(UTC),
                    )
                    self._write_result(result)
                    self._consumer.commit(asynchronous=False)
                    processed += 1
                    if processed % 100 == 0:
                        logger.info(
                            "[%s] processed=%d last_latency=%.1fms",
                            self.model_name, processed, latency_ms,
                        )
                except Exception as exc:
                    logger.warning("[%s] Failed to process message: %s", self.model_name, exc)
        finally:
            self._consumer.close()
            logger.info("[%s] Consumer closed. Total processed: %d", self.model_name, processed)

    def _handle_sigint(self, sig: int, frame: object) -> None:
        logger.info("[%s] Shutting down...", self.model_name)
        self._running = False
