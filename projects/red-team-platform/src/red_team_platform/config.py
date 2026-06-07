from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    sync_database_url: str
    pair_classifier_path: Path
    taxonomy_classifier_path: Path
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout_s: int = 120
    cluster_k: int = 8
    allowed_origins: str = "http://localhost:5173"
    api_port: int = 8003

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
