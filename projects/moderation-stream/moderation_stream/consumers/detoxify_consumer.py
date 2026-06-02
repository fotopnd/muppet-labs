from __future__ import annotations

import logging

from moderation_stream.config import Settings
from moderation_stream.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

_TOXICITY_THRESHOLD = 0.5


class DetoxifyConsumer(BaseConsumer):
    model_name = "detoxify"
    consumer_group_id = "consumer-detoxify"

    def _load_model(self) -> None:
        from detoxify import Detoxify

        self._model = Detoxify("original", device="cpu")

    def _run_inference(self, text: str) -> int:
        result = self._model.predict(text[:512])
        return 1 if result["toxicity"] >= _TOXICITY_THRESHOLD else 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    DetoxifyConsumer(Settings()).run()
