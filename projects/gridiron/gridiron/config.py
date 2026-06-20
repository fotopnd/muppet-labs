from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron"
    vite_origin: str = "http://localhost:5177"
    api_port: int = 8006


settings = Settings()
