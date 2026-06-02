from __future__ import annotations

import logging

from moderation_stream.config import Settings
from moderation_stream.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

_CANDIDATE_LABELS = ["toxic content", "safe content"]
_TOXIC_LABEL = "toxic content"


class DistilBertZeroShotConsumer(BaseConsumer):
    model_name = "distilbert-zero-shot"
    consumer_group_id = "consumer-distilbert"

    def _load_model(self) -> None:
        from transformers import pipeline

        self._pipe = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1,
        )

    def _run_inference(self, text: str) -> int:
        result = self._pipe(text[:512], candidate_labels=_CANDIDATE_LABELS)
        # labels are sorted by score descending — find by name, not index
        scores: dict[str, float] = dict(zip(result["labels"], result["scores"]))
        return 1 if scores.get(_TOXIC_LABEL, 0.0) >= 0.5 else 0


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    DistilBertZeroShotConsumer(Settings()).run()
