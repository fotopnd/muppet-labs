from __future__ import annotations

import logging
from pathlib import Path

from moderation_stream.config import Settings
from moderation_stream.consumers.base import BaseConsumer

logger = logging.getLogger(__name__)

# TODO: confirm label mapping with project 8 output
# Project 8 may export "LABEL_0"/"LABEL_1" (HuggingFace default) or "toxic"/"not toxic"
_POSITIVE_LABELS = {"LABEL_1", "toxic", "1"}


class FinetunedConsumer(BaseConsumer):
    def __init__(self, settings: Settings, checkpoint_path: Path | None) -> None:
        self._checkpoint_path = checkpoint_path
        super().__init__(settings)

    def _load_model(self) -> None:
        if self._checkpoint_path is None or not self._checkpoint_path.exists():
            logger.warning(
                "[%s] Checkpoint not found at %s — pending_weights mode.",
                self.model_name,
                self._checkpoint_path,
            )
            self._pipe = None
            return

        from transformers import pipeline

        self._pipe = pipeline(
            "text-classification",
            model=str(self._checkpoint_path),
            device=-1,
        )

    def _run_inference(self, text: str) -> int:
        if self._pipe is None:
            return 0
        result = self._pipe(text[:512])
        label = result[0]["label"] if isinstance(result, list) else result["label"]
        return 1 if label in _POSITIVE_LABELS else 0

    def run(self) -> None:
        if self._checkpoint_path is None or not self._checkpoint_path.exists():
            logger.warning("[%s] No checkpoint — exiting without consuming.", self.model_name)
            return
        super().run()


class FinetunedDistilBertConsumer(FinetunedConsumer):
    model_name = "distilbert-finetuned"
    consumer_group_id = "consumer-distilbert-ft"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings, settings.distilbert_checkpoint_path)


class FinetunedRobertaConsumer(FinetunedConsumer):
    model_name = "roberta-finetuned"
    consumer_group_id = "consumer-roberta-ft"

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings, settings.roberta_checkpoint_path)


def main_distilbert() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    FinetunedDistilBertConsumer(Settings()).run()


def main_roberta() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    FinetunedRobertaConsumer(Settings()).run()
