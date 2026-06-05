from __future__ import annotations

import argparse
import logging
import sys

from moderation_dashboard.config import MODEL_REGISTRY, get_settings

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Moderation dashboard consumer runner")
    parser.add_argument(
        "--model",
        required=True,
        choices=list(MODEL_REGISTRY.keys()),
        help="Which model to run",
    )
    parser.add_argument(
        "--mode",
        required=True,
        choices=["production", "shadow"],
        help="production = round-robin group; shadow = per-model group",
    )
    args = parser.parse_args()

    settings = get_settings()
    spec = MODEL_REGISTRY[args.model]

    group_id = (
        "moderation-production" if args.mode == "production" else f"moderation-shadow-{args.model}"
    )

    common = {
        "model_name": args.model,
        "group_id": group_id,
        "mode": args.mode,
        "bootstrap_servers": settings.kafka_bootstrap_servers,
        "topic": settings.kafka_topic,
        "db_url": settings.postgres_url_sync,
    }

    if args.model == "distilbert":
        from moderation_dashboard.consumers.distilbert import DistilBertZeroShotConsumer

        consumer = DistilBertZeroShotConsumer(**common)
    elif args.model == "roberta":
        from moderation_dashboard.consumers.roberta import RobertaZeroShotConsumer

        consumer = RobertaZeroShotConsumer(**common)
    elif args.model == "detoxify":
        from moderation_dashboard.consumers.detoxify_consumer import DetoxifyConsumer

        consumer = DetoxifyConsumer(**common)
    elif args.model == "finetuned_distilbert":
        checkpoint_path = settings.distilbert_checkpoint_path
        if checkpoint_path is None:
            logger.warning(
                "%s not set — exiting without consuming.",
                spec.checkpoint_path_env_var,
            )
            sys.exit(0)

        from moderation_dashboard.consumers.finetuned import FinetunedDistilBertConsumer

        consumer = FinetunedDistilBertConsumer(checkpoint_path=checkpoint_path, **common)
    else:
        logger.error("Unknown model: %s", args.model)
        sys.exit(1)

    logger.info("Starting %s consumer in group '%s'", args.model, group_id)
    consumer.run()
