from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5434/llm_safety_monitor"
    SYNC_DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5434/llm_safety_monitor"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC: str = "llm-interactions"

    # Model checkpoint paths — required at runtime for consumers
    PAIR_CLASSIFIER_PATH: Path = Path("/tmp/pair-classifier")
    PROMPT_DETECTOR_PATH: Path = Path("/tmp/prompt-detector")
    TAXONOMY_CLASSIFIER_PATH: Path = Path("/tmp/taxonomy-classifier")

    # Replay mix — env vars; must sum to ~1.0
    REPLAY_MIX_HHRLHF: float = 0.60
    REPLAY_MIX_WILDGUARD: float = 0.25
    REPLAY_MIX_ADVBENCH: float = 0.10
    REPLAY_MIX_JAILBREAKBENCH: float = 0.05

    # Case-queue integration
    CASE_QUEUE_URL: str = "http://localhost:8000"

    # Live Claude API mode
    LIVE_CLAUDE_MODE: bool = False
    ANTHROPIC_API_KEY: str = ""

    # API server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002

    @field_validator("REPLAY_MIX_HHRLHF", "REPLAY_MIX_WILDGUARD", "REPLAY_MIX_ADVBENCH", "REPLAY_MIX_JAILBREAKBENCH")
    @classmethod
    def _positive_weight(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Replay mix weights must be non-negative")
        return v


def get_settings() -> Settings:
    return Settings()
