from __future__ import annotations

from unittest.mock import MagicMock, patch

from moderation_stream.consumers.base import BaseConsumer
from moderation_stream.config import Settings


class _StubConsumer(BaseConsumer):
    model_name = "stub"
    consumer_group_id = "consumer-stub"

    def _load_model(self) -> None:
        pass

    def _run_inference(self, text: str) -> int:
        return 1 if "toxic" in text.lower() else 0


def _mock_settings() -> MagicMock:
    s = MagicMock(spec=Settings)
    s.kafka_bootstrap_servers = "localhost:9092"
    s.kafka_topic = "moderation-events"
    s.database_url = "postgresql://postgres:postgres@localhost:5433/moderation_stream_test"
    s.distilbert_checkpoint_path = None
    s.roberta_checkpoint_path = None
    return s


@patch("moderation_stream.consumers.base.Consumer")
@patch("moderation_stream.consumers.base.create_engine")
@patch("moderation_stream.consumers.base.sessionmaker")
def test_classify_returns_label_and_latency(mock_sm, mock_eng, mock_consumer) -> None:
    consumer = _StubConsumer(_mock_settings())
    label, latency_ms = consumer.classify("toxic comment here")
    assert label == 1
    assert latency_ms >= 0.0


@patch("moderation_stream.consumers.base.Consumer")
@patch("moderation_stream.consumers.base.create_engine")
@patch("moderation_stream.consumers.base.sessionmaker")
def test_classify_negative(mock_sm, mock_eng, mock_consumer) -> None:
    consumer = _StubConsumer(_mock_settings())
    label, _ = consumer.classify("great post, really helpful")
    assert label == 0


@patch("moderation_stream.consumers.base.Consumer")
@patch("moderation_stream.consumers.base.create_engine")
@patch("moderation_stream.consumers.base.sessionmaker")
def test_latency_is_non_negative(mock_sm, mock_eng, mock_consumer) -> None:
    consumer = _StubConsumer(_mock_settings())
    _, latency_ms = consumer.classify("any text")
    assert latency_ms >= 0.0
