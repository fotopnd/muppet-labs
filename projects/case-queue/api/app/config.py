from __future__ import annotations

from pydantic import model_validator
from pydantic_settings import BaseSettings

# CORS origins allowed in production — set ALLOWED_ORIGINS env var to override
_DEFAULT_ORIGINS = ["http://localhost:5173"]


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/case_queue"
    allowed_origins: list[str] = _DEFAULT_ORIGINS

    model_config = {"env_file": ".env", "extra": "ignore"}

    @model_validator(mode="after")
    def _normalise_database_url(self) -> Settings:
        # Fly.io Postgres sets DATABASE_URL as postgres:// or postgresql://
        # asyncpg requires the postgresql+asyncpg:// scheme
        url = self.database_url
        if url.startswith("postgres://"):
            self.database_url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            self.database_url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return self


settings = Settings()
