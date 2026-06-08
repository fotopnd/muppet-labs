from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import UTC, datetime
from typing import Literal, TypedDict

from llm_safety_monitor.config import Settings
from llm_safety_monitor.types import LLMInteractionEvent

logger = logging.getLogger(__name__)


class ClassifyResult(TypedDict):
    predicted_label: int
    confidence: float
    latency_ms: float
    taxonomy_labels: list[str] | None


class BaseConsumer:
    model_name: str
    # Overridden in Phase 2 when classifiers delegate to the shared llm-safety-classifier package.
    classifier_version: str = "legacy"

    def __init__(self, mode: Literal["production", "shadow"], model_name: str, settings: Settings) -> None:
        from sqlalchemy import create_engine

        self._mode = mode
        self.model_name = model_name
        self._settings = settings
        self._running = False
        self._engine = create_engine(settings.SYNC_DATABASE_URL)
        self._load_model()

    @abstractmethod
    def _load_model(self) -> None:
        """Load model checkpoint. Raises RuntimeError if path absent."""

    @abstractmethod
    def classify(self, text: str) -> ClassifyResult:
        """Classify text and return result dict."""

    def _write_classification(self, event: LLMInteractionEvent, result: ClassifyResult) -> None:
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy.orm import Session

        from llm_safety_monitor.api.models import ClassificationResult

        with Session(self._engine) as session:
            row = ClassificationResult(
                model_name=self.model_name,
                content=event.prompt[:500],
                predicted_label=result["predicted_label"],
                confidence=result["confidence"],
                latency_ms=result["latency_ms"],
                processed_at=datetime.now(UTC),
                seeded=False,
                event_id=event.event_id,
                taxonomy_labels=result.get("taxonomy_labels"),
                classifier_version=self.classifier_version,
            )
            try:
                session.add(row)
                session.commit()
            except IntegrityError:
                session.rollback()
                logger.debug(
                    "Duplicate classification skipped: event_id=%s model=%s version=%s",
                    event.event_id,
                    self.model_name,
                    self.classifier_version,
                )

    def _build_input_text(self, event: LLMInteractionEvent) -> str:
        from llm_safety_classifier import build_input_text

        return build_input_text(event.prompt, event.response)

    def run(self) -> None:
        from confluent_kafka import Consumer, KafkaError  # deferred

        consumer = Consumer(
            {
                "bootstrap.servers": self._settings.KAFKA_BOOTSTRAP_SERVERS,
                "group.id": f"{self.model_name}-shadow",
                "auto.offset.reset": "latest",
            }
        )
        consumer.subscribe([self._settings.KAFKA_TOPIC])
        self._running = True
        logger.info("%s consumer started", self.model_name)

        try:
            while self._running:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        logger.warning("%s Kafka error: %s", self.model_name, msg.error())
                    continue
                try:
                    event = LLMInteractionEvent.model_validate_json(msg.value())
                    text = self._build_input_text(event)
                    result = self.classify(text)
                    self._write_classification(event, result)
                    logger.debug(
                        "%s classified %s: label=%d conf=%.3f",
                        self.model_name,
                        event.event_id,
                        result["predicted_label"],
                        result["confidence"],
                    )
                except Exception as exc:
                    logger.warning("%s: error processing message: %s", self.model_name, exc, exc_info=True)
        finally:
            consumer.close()

    def stop(self) -> None:
        self._running = False
