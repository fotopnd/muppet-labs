from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from moderation_dashboard.consumers.base import BaseConsumer


class _FakeConsumer(BaseConsumer):
    """Minimal concrete subclass for testing BaseConsumer logic."""

    def __init__(self) -> None:
        # Skip Kafka/DB setup — patch at the class level
        self.model_name = "test-model"
        self._group_id = "moderation-production"
        self._topic = "test-topic"
        self._running = True
        self._Session = MagicMock()
        self._consumer = MagicMock()

    def classify(self, content: str) -> tuple[int, float]:
        return 1, 0.9


def test_consumer_classify_returns_label_and_confidence():
    consumer = _FakeConsumer()
    label, confidence = consumer.classify("bad content")
    assert label == 1
    assert confidence == 0.9


def test_consumer_classify_raises_if_not_implemented():
    class _BadConsumer(BaseConsumer):
        def __init__(self) -> None:
            self.model_name = "bad"
            self._group_id = "test"
            self._running = False

    with pytest.raises(TypeError):
        # Cannot instantiate abstract class without implementing classify
        _BadConsumer()


def test_write_result_calls_session():
    consumer = _FakeConsumer()
    mock_session_ctx = MagicMock()
    consumer._Session.return_value.__enter__ = MagicMock(return_value=mock_session_ctx)
    consumer._Session.return_value.__exit__ = MagicMock(return_value=False)

    fake_result = MagicMock()
    consumer._write_result(fake_result)

    mock_session_ctx.add.assert_called_once_with(fake_result)
    mock_session_ctx.commit.assert_called_once()


def test_detoxify_consumer_confidence_from_toxicity_score():
    """Detoxify confidence should be the raw toxicity score."""
    with patch(
        "moderation_dashboard.consumers.detoxify_consumer.DetoxifyConsumer.__init__",
        lambda self, *a, **kw: None,
    ):
        from moderation_dashboard.consumers.detoxify_consumer import DetoxifyConsumer

        consumer = object.__new__(DetoxifyConsumer)
        consumer._model = MagicMock()
        consumer._model.predict.return_value = {"toxicity": 0.75}
        consumer.model_name = "detoxify"

        label, conf = consumer.classify("offensive text")
        assert label == 1
        assert conf == pytest.approx(0.75)


def test_detoxify_consumer_low_score_returns_zero():
    with patch(
        "moderation_dashboard.consumers.detoxify_consumer.DetoxifyConsumer.__init__",
        lambda self, *a, **kw: None,
    ):
        from moderation_dashboard.consumers.detoxify_consumer import DetoxifyConsumer

        consumer = object.__new__(DetoxifyConsumer)
        consumer._model = MagicMock()
        consumer._model.predict.return_value = {"toxicity": 0.3}
        consumer.model_name = "detoxify"

        label, conf = consumer.classify("safe text")
        assert label == 0
        assert conf == pytest.approx(0.3)
