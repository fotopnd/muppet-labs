from __future__ import annotations

import logging
from dataclasses import dataclass

from red_team_platform.corpus.constants import (
    SEV_ATTACK_TEXT_FIELD,
    SEV_DATASET_NAME,
    SEV_HARM_GOAL_FIELD,
    SEV_SOURCE_KEY,
    SEV_SPLIT,
    SEV_STRATEGY_FIELD,
)

logger = logging.getLogger(__name__)


@dataclass
class AttackRecord:
    source: str
    source_id: str
    harm_category: str  # empty string from loader; set by seeder after taxonomy classification
    strategy: str
    attack_text: str
    harm_goal: str  # fed to taxonomy classifier; not persisted to DB


def load_sevdeawesome() -> list[AttackRecord]:
    """
    Loads sevdeawesome/jailbreak_success from HuggingFace (cached after first pull).
    Sets harm_goal from SEV_HARM_GOAL_FIELD; leaves harm_category as empty string.
    source_id = f"sev-{row_index}".
    Logs a warning and skips rows with missing required fields.
    """
    from datasets import load_dataset  # deferred — slow import

    try:
        ds = load_dataset(SEV_DATASET_NAME, split=SEV_SPLIT)
    except ValueError:
        # Some datasets require an explicit config name
        from datasets import get_dataset_config_names

        configs = get_dataset_config_names(SEV_DATASET_NAME)
        if not configs:
            raise RuntimeError(f"No configs found for dataset {SEV_DATASET_NAME}") from None
        ds = load_dataset(SEV_DATASET_NAME, configs[0], split=SEV_SPLIT)

    records: list[AttackRecord] = []
    skipped = 0
    for idx, row in enumerate(ds):  # type: ignore[arg-type]
        attack_text = row.get(SEV_ATTACK_TEXT_FIELD)
        strategy = row.get(SEV_STRATEGY_FIELD)
        harm_goal = row.get(SEV_HARM_GOAL_FIELD)

        if not attack_text or not strategy or not harm_goal:
            logger.warning("sevdeawesome: skipped row %d (missing required fields)", idx)
            skipped += 1
            continue

        records.append(
            AttackRecord(
                source=SEV_SOURCE_KEY,
                source_id=f"sev-{idx}",
                harm_category="",
                strategy=str(strategy).strip(),
                attack_text=str(attack_text).strip(),
                harm_goal=str(harm_goal).strip(),
            )
        )

    if skipped:
        logger.warning("sevdeawesome: skipped %d malformed examples total", skipped)

    return records
