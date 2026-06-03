from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jigsaw_data_dir: Path = Path("data")
    model_output_dir: Path = Path("checkpoints")
