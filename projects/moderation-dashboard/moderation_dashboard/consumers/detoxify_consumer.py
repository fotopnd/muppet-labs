from __future__ import annotations

import logging

from moderation_dashboard.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

_TOXICITY_THRESHOLD = 0.5


class DetoxifyConsumer(BaseConsumer):
    def __init__(
        self, model_name: str, group_id: str, bootstrap_servers: str, topic: str, db_url: str
    ) -> None:
        super().__init__(model_name, group_id, bootstrap_servers, topic, db_url)
        from detoxify import Detoxify

        logger.info("Loading Detoxify model...")
        self._model = Detoxify("original", device="cpu")
        logger.info("Detoxify ready.")

    def classify(self, content: str) -> tuple[int, float]:
        result = self._model.predict(content[:512])
        confidence = float(result["toxicity"])
        return (1 if confidence >= _TOXICITY_THRESHOLD else 0), confidence
