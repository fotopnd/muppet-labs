"""seed_sim.py — Pre-seed 10k Jigsaw events with all 5 models for the demo deployment.

Loads rows 0-9999 from the Jigsaw CSV, runs each model at device=-1 (CPU) in sequence,
and writes results to the local Postgres DB with seeded=True and group='production'.

One model is loaded at a time to bound peak RAM. Fine-tuned models skip gracefully if
their checkpoint paths are not configured in .env.

Run with: uv run seed-sim --confirm
"""

from __future__ import annotations

import argparse
import csv
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from moderation_dashboard.api.models import Classification
from moderation_dashboard.config import MODEL_REGISTRY, get_settings
from moderation_dashboard.producer import get_primary_category

logger = logging.getLogger(__name__)

SEED_LIMIT = 10_000
BATCH_SIZE = 500  # commit rows to DB in batches


def load_rows(path: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            if idx >= limit:
                break
            content = row.get("comment_text", "").strip()
            if not content:
                continue
            rows.append({**row, "_idx": idx})
    return rows


def write_batch(session_factory: Any, records: list[Classification]) -> None:
    with session_factory() as session:
        session.add_all(records)
        session.commit()


def seed_model(
    model_key: str,
    rows: list[dict[str, Any]],
    session_factory: Any,
) -> int:
    spec = MODEL_REGISTRY[model_key]
    settings = get_settings()

    # Idempotency: remove any previously seeded rows for this model before re-seeding
    with session_factory() as session:
        result = session.execute(
            text(
                "DELETE FROM classifications WHERE seeded = true AND model_name = :mk RETURNING id"
            ),
            {"mk": model_key},
        )
        deleted_count = len(result.fetchall())
        session.commit()
    if deleted_count:
        logger.info("[%s] Deleted %d previously seeded rows", model_key, deleted_count)

    # Build classifier function
    if model_key == "distilbert":
        from transformers import pipeline as hf_pipeline

        logger.info("Loading DistilBERT zero-shot...")
        pipe = hf_pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1,
        )

        def classify(content: str) -> tuple[int, float]:
            result = pipe(content[:512], candidate_labels=["toxic content", "safe content"])
            scores: dict[str, float] = dict(zip(result["labels"], result["scores"], strict=True))
            conf = scores.get("toxic content", 0.0)
            return (1 if conf >= 0.5 else 0), conf

    elif model_key == "roberta":
        from transformers import pipeline as hf_pipeline

        logger.info("Loading RoBERTa zero-shot...")
        pipe = hf_pipeline(
            "zero-shot-classification",
            model="roberta-large-mnli",
            device=-1,
        )

        def classify(content: str) -> tuple[int, float]:
            result = pipe(content[:512], candidate_labels=["toxic content", "safe content"])
            scores: dict[str, float] = dict(zip(result["labels"], result["scores"], strict=True))
            conf = scores.get("toxic content", 0.0)
            return (1 if conf >= 0.5 else 0), conf

    elif model_key == "detoxify":
        from detoxify import Detoxify

        logger.info("Loading Detoxify...")
        model = Detoxify("original", device="cpu")

        def classify(content: str) -> tuple[int, float]:
            result = model.predict(content[:512])
            conf = float(result["toxicity"])
            return (1 if conf >= 0.5 else 0), conf

    elif model_key == "finetuned_distilbert":
        checkpoint_path = settings.distilbert_checkpoint_path
        if checkpoint_path is None:
            logger.warning(
                "%s not set — skipping %s (%d previously seeded rows deleted, none written)",
                spec.checkpoint_path_env_var,
                model_key,
                deleted_count,
            )
            return 0

        from transformers import pipeline as hf_pipeline

        logger.info("Loading fine-tuned DistilBERT from %s...", checkpoint_path)
        pipe = hf_pipeline("text-classification", model=str(checkpoint_path), device=-1)
        _positive_labels = {"LABEL_1", "toxic", "1"}

        def classify(content: str) -> tuple[int, float]:
            result = pipe(content[:512])
            item = result[0] if isinstance(result, list) else result
            label: str = item["label"]
            score: float = float(item["score"])
            predicted = 1 if label in _positive_labels else 0
            return predicted, score

    else:
        raise ValueError(f"Unknown model key: {model_key!r}")

    logger.info("Seeding %d rows for model=%s...", len(rows), model_key)
    t_start = time.monotonic()
    batch: list[Classification] = []
    written = 0
    # Spread created_at across the past 24 hours so analytics charts never expire
    seed_base_time = datetime.now(UTC) - timedelta(hours=24)
    n_rows = max(len(rows) - 1, 1)

    for i, raw in enumerate(rows):
        content = raw["comment_text"].strip()
        ground_truth = int(float(raw.get("toxic", 0)))
        category = get_primary_category(raw)

        t0 = time.perf_counter()
        predicted_label, confidence = classify(content)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        correct = predicted_label == ground_truth

        batch.append(
            Classification(
                id=str(uuid.uuid4()),
                event_id=str(uuid.uuid5(uuid.NAMESPACE_OID, f"seed-{raw['_idx']}")),
                group="production",
                model_name=model_key,
                category=category,
                content=content,
                predicted_label=predicted_label,
                confidence=confidence,
                latency_ms=latency_ms,
                correct=correct,
                created_at=seed_base_time + timedelta(seconds=86400 * i / n_rows),
                seeded=True,
            )
        )

        if len(batch) >= BATCH_SIZE:
            write_batch(session_factory, batch)
            written += len(batch)
            batch = []
            elapsed = time.monotonic() - t_start
            logger.info(
                "[%s] %d/%d written (%.1fs elapsed)",
                model_key,
                written,
                len(rows),
                elapsed,
            )

    if batch:
        write_batch(session_factory, batch)
        written += len(batch)

    elapsed = time.monotonic() - t_start
    logger.info("[%s] Done. %d rows written in %.1fs.", model_key, written, elapsed)
    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Seed 10k Jigsaw events with all 5 models")
    parser.add_argument(
        "--confirm",
        action="store_true",
        required=True,
        help="Required flag — confirms you intend to write seeded data to the local DB",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=SEED_LIMIT,
        help=f"Number of Jigsaw rows to seed (default: {SEED_LIMIT})",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=list(MODEL_REGISTRY.keys()),
        default=list(MODEL_REGISTRY.keys()),
        help="Which models to seed (default: all 5)",
    )
    args = parser.parse_args()

    settings = get_settings()
    csv_path = Path(settings.jigsaw_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Jigsaw CSV not found at {csv_path}. "
            "Download it from Kaggle: jigsaw-toxic-comment-classification-challenge"
        )

    logger.info("Loading %d rows from %s...", args.limit, csv_path)
    rows = load_rows(csv_path, args.limit)
    logger.info("Loaded %d rows.", len(rows))

    engine = create_engine(settings.postgres_url_sync)
    session_factory = sessionmaker(bind=engine)

    total_written = 0
    for model_key in args.models:
        n = seed_model(model_key, rows, session_factory)
        total_written += n

    logger.info("Seed complete. Total rows written: %d", total_written)
    logger.info(
        "\nTo export the seeded DB for VPS restore, run:\n"
        "  pg_dump -h localhost -p 5434 -U postgres moderation_dashboard "
        "> moderation_dashboard_seeded.sql\n"
        "Then on the VPS:\n"
        "  psql -h localhost -U postgres moderation_dashboard "
        "< moderation_dashboard_seeded.sql"
    )


if __name__ == "__main__":
    main()
