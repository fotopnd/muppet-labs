from __future__ import annotations

import logging
import signal
import threading

from llm_safety_monitor.config import get_settings
from llm_safety_monitor.consumers.pair_classifier import PairSafetyClassifier
from llm_safety_monitor.consumers.prompt_detector import PromptAdversarialDetector
from llm_safety_monitor.consumers.taxonomy_classifier import HarmTaxonomyClassifier
from llm_safety_monitor.escalation.router import EscalationPoller

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()

    pair = PairSafetyClassifier(settings)
    prompt = PromptAdversarialDetector(settings)
    taxonomy = HarmTaxonomyClassifier(settings)
    poller = EscalationPoller(settings)

    threads = [
        threading.Thread(target=pair.run, daemon=True, name="pair-consumer"),
        threading.Thread(target=prompt.run, daemon=True, name="prompt-consumer"),
        threading.Thread(target=taxonomy.run, daemon=True, name="taxonomy-consumer"),
        threading.Thread(target=poller.run, daemon=True, name="escalation-poller"),
    ]

    def _shutdown(sig: int, frame: object) -> None:
        logger.info("Shutting down consumers...")
        pair.stop()
        prompt.stop()
        taxonomy.stop()
        poller.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    for t in threads:
        t.start()
        logger.info("Started thread: %s", t.name)

    for t in threads:
        t.join()

    logger.info("All consumers stopped")
