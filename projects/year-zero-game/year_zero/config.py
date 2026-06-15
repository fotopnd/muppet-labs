from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://year_zero:year_zero@localhost:5437/year_zero"
    ollama_url: str = "http://localhost:11434"
    vite_origin: str = "http://localhost:5175"
    api_port: int = 8005


settings = Settings()
