from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict

MODEL_REGISTRY: list[dict[str, Any]] = [
    {"model_name": "distilbert-zero-shot", "phase": 1},
    {"model_name": "roberta-zero-shot", "phase": 1},
    {"model_name": "detoxify", "phase": 1},
    {"model_name": "distilbert-finetuned", "phase": 2, "checkpoint_field": "distilbert_checkpoint_path"},
    {"model_name": "roberta-finetuned", "phase": 2, "checkpoint_field": "roberta_checkpoint_path"},
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "moderation-events"
    database_url: str = "postgresql://postgres:postgres@localhost:5433/moderation_stream_db"
    async_database_url: str | None = None
    jigsaw_csv_path: Path = Path("data/train.csv")
    producer_rate_per_sec: int = 10
    allowed_origin: str = "http://localhost:5173"
    distilbert_checkpoint_path: Path | None = None
    roberta_checkpoint_path: Path | None = None

    @property
    def effective_async_database_url(self) -> str:
        if self.async_database_url:
            return self.async_database_url
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
