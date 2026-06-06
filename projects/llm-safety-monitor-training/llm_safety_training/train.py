"""Unified training entry point — dispatches to per-model training functions.

Usage:
    uv run train --model pair    --output-dir <dir> [--epochs 4] [--batch-size 128] [--max-train-samples N]
    uv run train --model prompt  --output-dir <dir> [--epochs 4] [--batch-size 128] [--max-train-samples N]
    uv run train --model taxonomy --output-dir <dir> [--epochs 4] [--batch-size 64]  [--max-train-samples N]
"""
from __future__ import annotations

import argparse
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_BATCH = {"pair": 128, "prompt": 128, "taxonomy": 64}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Train an LLM safety classifier")
    parser.add_argument("--model", required=True, choices=["pair", "prompt", "taxonomy"])
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Checkpoint output directory (defaults to checkpoints/<model>-<date>)",
    )
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-train-samples", type=int, default=None)
    args = parser.parse_args()

    output_dir = args.output_dir or Path(
        f"checkpoints/{args.model}-{datetime.now(UTC).strftime('%Y-%m-%d')}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    batch_size = args.batch_size or _DEFAULT_BATCH[args.model]

    logger.info("Training model=%s output_dir=%s epochs=%d batch_size=%d", args.model, output_dir, args.epochs, batch_size)

    if args.model == "pair":
        from llm_safety_training.train_pair import train
    elif args.model == "prompt":
        from llm_safety_training.train_prompt import train
    else:
        from llm_safety_training.train_taxonomy import train

    train(
        output_dir=output_dir,
        epochs=args.epochs,
        batch_size=batch_size,
        seed=args.seed,
        max_train_samples=args.max_train_samples,
    )
