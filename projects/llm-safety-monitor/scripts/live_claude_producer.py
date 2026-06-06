"""Optional live Claude API mode producer.

Sends benign prompts to Haiku, receives responses, injects the pair as
source_dataset="live" events. Only enable during demos with LIVE_CLAUDE_MODE=true.
NOT for adversarial content — only benign prompts go to Claude.
"""
from __future__ import annotations

import logging
import signal
import time
from uuid import uuid4

logger = logging.getLogger(__name__)

BENIGN_PROMPTS = [
    "What's a good recipe for chocolate chip cookies?",
    "Can you explain how photosynthesis works?",
    "What are some tips for learning a new language?",
    "How does a car engine work?",
    "Tell me about the history of the internet.",
]


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    from llm_safety_monitor.config import get_settings
    from llm_safety_monitor.types import LLMInteractionEvent, SourceDataset

    settings = get_settings()
    if not settings.LIVE_CLAUDE_MODE:
        logger.info("LIVE_CLAUDE_MODE is false — nothing to do. Set LIVE_CLAUDE_MODE=true to enable.")
        return

    import anthropic  # deferred
    from confluent_kafka import Producer  # deferred
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from llm_safety_monitor.api.models import Interaction

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})
    engine = create_engine(settings.SYNC_DATABASE_URL)

    running = True

    def _shutdown(sig: int, frame: object) -> None:
        nonlocal running
        logger.info("Shutting down live producer")
        running = False

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    import itertools

    prompt_cycle = itertools.cycle(BENIGN_PROMPTS)
    logger.info("Live Claude producer started (Haiku 3.5, benign prompts only)")

    while running:
        prompt = next(prompt_cycle)
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = message.content[0].text if message.content else ""

            event = LLMInteractionEvent(
                event_id=uuid4(),
                prompt=prompt,
                response=response_text,
                source_dataset=SourceDataset.LIVE,
                ground_truth_safe=None,
                ground_truth_categories=None,
            )

            with Session(engine) as session:
                session.add(Interaction(
                    id=event.event_id,
                    prompt_text=event.prompt,
                    response_text=event.response,
                    source_dataset=event.source_dataset.value,
                    ground_truth_safe=None,
                    ground_truth_categories=None,
                ))
                session.commit()

            producer.produce(
                settings.KAFKA_TOPIC,
                key=str(event.event_id),
                value=event.model_dump_json(),
            )
            producer.poll(0)
            logger.info("Live event published: %s", event.event_id)

        except Exception as exc:
            logger.warning("Live producer error: %s", exc, exc_info=True)

        time.sleep(60)  # 1 call/minute to stay within demo budget

    producer.flush()


if __name__ == "__main__":
    main()
