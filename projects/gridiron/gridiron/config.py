from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron"
    vite_origin: str = "http://localhost:5177"
    api_port: int = 8006
    dev_replay_game_id: int | None = None

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg2")


settings = Settings()

PLAYS_PER_GAME: int = 135
EMIT_INTERVAL: float = 600 / PLAYS_PER_GAME  # ~4.44 s per play in SSE replay
