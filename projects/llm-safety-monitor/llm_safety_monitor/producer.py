from __future__ import annotations

import itertools
import json
import logging
import random
import signal
import time
from uuid import uuid4

from llm_safety_monitor.config import Settings, get_settings
from llm_safety_monitor.types import LLMInteractionEvent, SourceDataset

logger = logging.getLogger(__name__)

TICK_SECONDS = 3.0


def _load_datasets() -> dict[SourceDataset, list[dict]]:
    """Load all four replay datasets into memory. Deferred imports for slow HF loads."""
    from datasets import load_dataset  # deferred

    logger.info("Loading HH-RLHF...")
    hh_ds = load_dataset("Anthropic/hh-rlhf", split="train")
    hh_rows = [
        {
            "prompt": _extract_final_human(row["chosen"]),
            "response": _extract_final_assistant(row["chosen"]),
            "ground_truth_safe": True,
            "ground_truth_categories": None,
        }
        for row in hh_ds
        if _extract_final_human(row["chosen"])
    ][:50000]  # cap at 50k for memory

    logger.info("Loading WildGuard...")
    wg_ds = load_dataset("allenai/wildguard", split="train")
    wg_rows = [
        {
            "prompt": (row.get("prompt") or "").strip(),
            "response": (row.get("response") or "").strip() or None,
            "ground_truth_safe": row.get("response_harm_label") != "harmful",
            "ground_truth_categories": (
                [row["subcategory"]] if row.get("subcategory") and row.get("response_harm_label") == "harmful" else None
            ),
        }
        for row in wg_ds
        if (row.get("prompt") or "").strip()
    ]

    logger.info("Loading AdvBench...")
    adv_ds = load_dataset("llm-attacks/AdvBench", split="train")
    adv_rows = [
        {
            "prompt": row["goal"].strip(),
            "response": None,
            "ground_truth_safe": False,
            "ground_truth_categories": None,
        }
        for row in adv_ds
        if row.get("goal")
    ]

    logger.info("Loading JailbreakBench...")
    jbb_ds = load_dataset("JailbreakBench/JailbreakBench-artifacts", split="train")
    jbb_rows = [
        {
            "prompt": row["prompt"].strip(),
            "response": None,
            "ground_truth_safe": False,
            "ground_truth_categories": None,
        }
        for row in jbb_ds
        if row.get("prompt")
    ]

    logger.info(
        "Datasets loaded: HH-RLHF=%d WildGuard=%d AdvBench=%d JailbreakBench=%d",
        len(hh_rows),
        len(wg_rows),
        len(adv_rows),
        len(jbb_rows),
    )

    return {
        SourceDataset.HH_RLHF: hh_rows,
        SourceDataset.WILDGUARD: wg_rows,
        SourceDataset.ADVBENCH: adv_rows,
        SourceDataset.JAILBREAKBENCH: jbb_rows,
    }


def _extract_final_human(field: str) -> str:
    parts = field.split("\n\nHuman: ")
    if len(parts) < 2:
        return ""
    last = parts[-1].split("\n\nAssistant: ")[0]
    return last.strip()


def _extract_final_assistant(field: str) -> str:
    parts = field.split("\n\nAssistant: ")
    if len(parts) < 2:
        return ""
    return parts[-1].strip()


class ReplayProducer:
    def __init__(self, settings: Settings) -> None:
        from confluent_kafka import Producer  # deferred

        self._settings = settings
        self._running = False
        self._producer = Producer({"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS})

        datasets = _load_datasets()
        for rows in datasets.values():
            random.shuffle(rows)

        self._cycles = {source: itertools.cycle(rows) for source, rows in datasets.items()}
        self._weights = [
            settings.REPLAY_MIX_HHRLHF,
            settings.REPLAY_MIX_WILDGUARD,
            settings.REPLAY_MIX_ADVBENCH,
            settings.REPLAY_MIX_JAILBREAKBENCH,
        ]
        self._sources = [
            SourceDataset.HH_RLHF,
            SourceDataset.WILDGUARD,
            SourceDataset.ADVBENCH,
            SourceDataset.JAILBREAKBENCH,
        ]

    def _write_interaction(self, event: LLMInteractionEvent) -> None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from llm_safety_monitor.api.models import Interaction

        engine = create_engine(self._settings.SYNC_DATABASE_URL)
        with Session(engine) as session:
            interaction = Interaction(
                id=event.event_id,
                prompt_text=event.prompt,
                response_text=event.response,
                source_dataset=event.source_dataset.value,
                ground_truth_safe=event.ground_truth_safe,
                ground_truth_categories=(
                    event.ground_truth_categories
                    if event.ground_truth_categories is not None
                    else None
                ),
            )
            session.add(interaction)
            session.commit()

    def run(self) -> None:
        self._running = True
        logger.info("Replay producer starting on topic %s", self._settings.KAFKA_TOPIC)

        while self._running:
            [source] = random.choices(self._sources, weights=self._weights, k=1)
            row = next(self._cycles[source])

            event = LLMInteractionEvent(
                event_id=uuid4(),
                prompt=row["prompt"],
                response=row.get("response"),
                source_dataset=source,
                ground_truth_safe=row.get("ground_truth_safe"),
                ground_truth_categories=row.get("ground_truth_categories"),
            )

            try:
                self._write_interaction(event)
                payload = event.model_dump_json()
                self._producer.produce(
                    self._settings.KAFKA_TOPIC,
                    key=str(event.event_id),
                    value=payload,
                )
                self._producer.poll(0)
                logger.debug("Published event %s from %s", event.event_id, source)
            except Exception as exc:
                logger.warning("Producer error: %s", exc, exc_info=True)

            time.sleep(TICK_SECONDS)

        self._producer.flush()

    def stop(self) -> None:
        self._running = False


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    producer = ReplayProducer(settings)

    def _shutdown(sig: int, frame: object) -> None:
        logger.info("Shutting down producer...")
        producer.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)
    producer.run()
