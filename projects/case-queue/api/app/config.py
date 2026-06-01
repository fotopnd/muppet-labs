from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
