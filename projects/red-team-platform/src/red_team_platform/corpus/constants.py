from __future__ import annotations

# sevdeawesome/jailbreak_success field names
# Implementer: verify by running:
#   from datasets import load_dataset
#   ds = load_dataset("sevdeawesome/jailbreak_success", split="train[:5]")
#   print(ds.features); print(ds[0])
# Update these constants if field names differ.
SEV_DATASET_NAME = "sevdeawesome/jailbreak_success"
SEV_SPLIT = "train"
SEV_ATTACK_TEXT_FIELD = "jailbreak_query"
SEV_STRATEGY_FIELD = "strategy"
SEV_HARM_GOAL_FIELD = "behavior"
SEV_SOURCE_KEY = "sevdeawesome"
