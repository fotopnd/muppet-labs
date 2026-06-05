from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass
class ModelSpec:
    model_key: str
    display_name: str
    requires_checkpoint: bool
    checkpoint_path_env_var: str | None  # None for zero-shot models


MODEL_REGISTRY: dict[str, ModelSpec] = {
    "distilbert": ModelSpec("distilbert", "DistilBERT (zero-shot)", False, None),
    "detoxify": ModelSpec("detoxify", "Detoxify", False, None),
    "finetuned_distilbert": ModelSpec(
        "finetuned_distilbert", "DistilBERT (fine-tuned)", True, "DISTILBERT_CHECKPOINT_PATH"
    ),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9093"
    kafka_topic: str = "moderation-events"
    kafka_num_partitions: int = 5

    # Postgres — sync for consumers/anomaly/escalation, async for API
    postgres_url_sync: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5434/moderation_dashboard"
    )
    postgres_url_async: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5434/moderation_dashboard"
    )

    # Producer
    jigsaw_csv_path: Path = Path("data/train.csv")
    producer_rate_per_sec: float = 10.0

    # Escalation
    escalation_confidence_threshold: float = 0.6
    escalation_poll_interval_secs: float = 10.0
    case_queue_api_url: str = "http://localhost:8000"

    # Anomaly detection
    anomaly_zscore_threshold: float = 3.0
    anomaly_window_minutes: int = 5
    anomaly_min_history_windows: int = 10

    # API
    cors_origins: list[str] = ["http://localhost:5174"]

    # dbt
    dbt_project_dir: Path = Path("dbt")

    # Phase 2 checkpoints (None = pending_weights)
    distilbert_checkpoint_path: Path | None = None

    # Demo config
    # Models with live consumers on this deployment. Used to label metrics as 'live' vs 'seeded'.
    # On VPS deploy, set LIVE_MODELS='["distilbert","detoxify"]' in .env
    live_models: list[str] = ["distilbert", "detoxify"]
    sparkline_window_size: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
