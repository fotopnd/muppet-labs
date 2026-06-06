from __future__ import annotations

import logging
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Verify these names against the actual WildGuard dataset schema:
#   from datasets import load_dataset
#   ds = load_dataset("allenai/wildguard", split="train")
#   print(ds.features)
# Update WILDGUARD_CATEGORIES to match the exact subcategory strings in the dataset.
WILDGUARD_CATEGORIES: tuple[str, ...] = (
    "Violent Crimes",
    "Non-Violent Crimes",
    "Sex-Related Crimes",
    "Child Sexual Exploitation",
    "Specialized Advice",
    "Privacy",
    "Intellectual Property",
    "Indiscriminate Weapons",
    "Hate",
    "Self-Harm",
    "Sexual Content",
    "Elections",
    "Disinformation",
)
NUM_HARM_CATEGORIES: int = len(WILDGUARD_CATEGORIES)
CATEGORY_TO_IDX: dict[str, int] = {c: i for i, c in enumerate(WILDGUARD_CATEGORIES)}


@dataclass
class WildGuardSplits:
    pair_train_texts: list[str]
    pair_train_labels: list[int]
    pair_eval_texts: list[str]
    pair_eval_labels: list[int]
    taxonomy_train_texts: list[str]
    taxonomy_train_labels: list[list[int]]  # 13-dim binary vectors
    taxonomy_eval_texts: list[str]
    taxonomy_eval_labels: list[list[int]]


def _extract_hhrlhf_pair(field: str) -> str | None:
    """Extract 'final human turn [SEP] final assistant turn' from a HH-RLHF string.

    Returns None if parsing fails (malformed field).
    """
    try:
        parts = field.split("\n\nHuman: ")
        if len(parts) < 2:
            return None
        last_human_onward = parts[-1]
        human_parts = last_human_onward.split("\n\nAssistant: ")
        if len(human_parts) < 2:
            return None
        human_turn = human_parts[0].strip()
        assistant_turn = human_parts[-1].strip()
        return f"{human_turn} [SEP] {assistant_turn}"
    except Exception:
        return None


def load_hhrlhf_binary(split: str = "train") -> tuple[list[str], list[int]]:
    """Load HH-RLHF as binary safe/unsafe pairs.

    chosen → label 0 (safe response), rejected → label 1 (unsafe response).
    """
    from datasets import load_dataset  # deferred: slow import

    ds = load_dataset("Anthropic/hh-rlhf", split=split)
    texts: list[str] = []
    labels: list[int] = []
    skipped = 0
    for row in ds:
        for field, label in [(row["chosen"], 0), (row["rejected"], 1)]:
            text = _extract_hhrlhf_pair(field)
            if text is None:
                skipped += 1
                continue
            texts.append(text)
            labels.append(label)
    if skipped:
        logger.warning("HH-RLHF: skipped %d malformed examples", skipped)
    return texts, labels


def split_wildguard(seed: int = 42) -> WildGuardSplits:
    """Split WildGuard 70/30 at example level with a fixed seed.

    Each allocation reserves 10% as held-out eval before the 70/30 split is applied.
    No example appears in more than one training set.
    """
    from datasets import load_dataset  # deferred: slow import

    ds = load_dataset("allenai/wildguard", split="train")
    rng = random.Random(seed)

    all_indices = list(range(len(ds)))
    rng.shuffle(all_indices)

    # Reserve 10% overall as a shared held-out pool, then split remainder 70/30
    held_out_n = int(len(all_indices) * 0.10)
    pair_train_n = int(len(all_indices) * 0.63)  # 70% of remaining 90%

    held_out_indices = all_indices[:held_out_n]
    pair_train_indices = all_indices[held_out_n : held_out_n + pair_train_n]
    taxonomy_train_indices = all_indices[held_out_n + pair_train_n :]

    def _make_pair_example(row: dict) -> tuple[str, int] | None:
        prompt = (row.get("prompt") or "").strip()
        response = (row.get("response") or "").strip()
        if not prompt:
            return None
        text = f"{prompt} [SEP] {response}" if response else prompt
        label = 1 if row.get("response_harm_label") == "harmful" else 0
        return text, label

    def _make_taxonomy_example(row: dict) -> tuple[str, list[int]] | None:
        prompt = (row.get("prompt") or "").strip()
        response = (row.get("response") or "").strip()
        if not prompt:
            return None
        text = f"{prompt} [SEP] {response}" if response else prompt
        category = row.get("subcategory") or row.get("category") or ""
        label_vec = [0] * NUM_HARM_CATEGORIES
        if category in CATEGORY_TO_IDX:
            label_vec[CATEGORY_TO_IDX[category]] = 1
        else:
            # Unknown category: all zeros — still valid for multi-label training
            logger.debug("Unknown WildGuard category: %r", category)
        return text, label_vec

    pair_train_texts, pair_train_labels = [], []
    for idx in pair_train_indices:
        row = ds[idx]
        result = _make_pair_example(row)
        if result:
            pair_train_texts.append(result[0])
            pair_train_labels.append(result[1])

    taxonomy_train_texts, taxonomy_train_labels = [], []
    for idx in taxonomy_train_indices:
        row = ds[idx]
        result = _make_taxonomy_example(row)
        if result:
            taxonomy_train_texts.append(result[0])
            taxonomy_train_labels.append(result[1])

    # Held-out: split evenly for pair eval and taxonomy eval
    mid = len(held_out_indices) // 2
    pair_eval_texts, pair_eval_labels = [], []
    for idx in held_out_indices[:mid]:
        row = ds[idx]
        result = _make_pair_example(row)
        if result:
            pair_eval_texts.append(result[0])
            pair_eval_labels.append(result[1])

    taxonomy_eval_texts, taxonomy_eval_labels = [], []
    for idx in held_out_indices[mid:]:
        row = ds[idx]
        result = _make_taxonomy_example(row)
        if result:
            taxonomy_eval_texts.append(result[0])
            taxonomy_eval_labels.append(result[1])

    return WildGuardSplits(
        pair_train_texts=pair_train_texts,
        pair_train_labels=pair_train_labels,
        pair_eval_texts=pair_eval_texts,
        pair_eval_labels=pair_eval_labels,
        taxonomy_train_texts=taxonomy_train_texts,
        taxonomy_train_labels=taxonomy_train_labels,
        taxonomy_eval_texts=taxonomy_eval_texts,
        taxonomy_eval_labels=taxonomy_eval_labels,
    )


def load_advbench() -> tuple[list[str], list[int]]:
    """Load AdvBench harmful instructions. All positives (label=1)."""
    from datasets import load_dataset  # deferred: slow import

    ds = load_dataset("llm-attacks/AdvBench", split="train")
    texts = [row["goal"].strip() for row in ds if row.get("goal")]
    labels = [1] * len(texts)
    return texts, labels


def load_jailbreakbench() -> tuple[list[str], list[int]]:
    """Load JailbreakBench adversarial prompts. All positives (label=1)."""
    from datasets import load_dataset  # deferred: slow import

    # JailbreakBench artifacts — prompt variants per behavior
    ds = load_dataset("JailbreakBench/JailbreakBench-artifacts", split="train")
    texts = [row["prompt"].strip() for row in ds if row.get("prompt")]
    labels = [1] * len(texts)
    return texts, labels


def build_prompt_detector_dataset(
    seed: int = 42,
) -> tuple[list[str], list[int], list[str], list[int]]:
    """Build balanced binary dataset for the prompt adversarial detector.

    Positives: AdvBench + JailbreakBench + WildGuard harmful prompt-only examples (subset).
    Negatives: HH-RLHF chosen-side conversation openers + WildGuard safe prompts.

    WildGuard examples drawn from the pair_train 70% allocation only — the taxonomy 30%
    is reserved for the taxonomy classifier and must not bleed into this dataset.

    Returns: (train_texts, train_labels, eval_texts, eval_labels)
    """
    from datasets import load_dataset  # deferred: slow import

    rng = random.Random(seed)

    # Positives
    adv_texts, adv_labels = load_advbench()
    jbb_texts, jbb_labels = load_jailbreakbench()

    # WildGuard harmful prompts from the pair_train split
    wg_splits = split_wildguard(seed=seed)
    wg_harmful_texts = [
        t.split(" [SEP] ")[0]
        for t, lbl in zip(wg_splits.pair_train_texts, wg_splits.pair_train_labels)
        if lbl == 1
    ]

    all_positive_texts = adv_texts + jbb_texts + wg_harmful_texts
    rng.shuffle(all_positive_texts)
    n_pos = len(all_positive_texts)

    # Negatives: HH-RLHF chosen prompts (extract the human side only)
    ds_hh = load_dataset("Anthropic/hh-rlhf", split="train")
    neg_texts: list[str] = []
    for row in ds_hh:
        text = _extract_hhrlhf_pair(row["chosen"])
        if text:
            neg_texts.append(text.split(" [SEP] ")[0])  # prompt side only
        if len(neg_texts) >= n_pos * 2:
            break

    # WildGuard safe prompts
    wg_safe_texts = [
        t.split(" [SEP] ")[0]
        for t, lbl in zip(wg_splits.pair_train_texts, wg_splits.pair_train_labels)
        if lbl == 0
    ]
    neg_texts += wg_safe_texts
    rng.shuffle(neg_texts)
    neg_texts = neg_texts[:n_pos]

    all_texts = all_positive_texts + neg_texts
    all_labels = [1] * n_pos + [0] * len(neg_texts)

    # Shuffle and split 80/20 train/eval
    combined = list(zip(all_texts, all_labels))
    rng.shuffle(combined)
    split_n = int(len(combined) * 0.80)
    train = combined[:split_n]
    eval_ = combined[split_n:]

    train_texts = [t for t, _ in train]
    train_labels = [l for _, l in train]
    eval_texts = [t for t, _ in eval_]
    eval_labels = [l for _, l in eval_]

    return train_texts, train_labels, eval_texts, eval_labels
