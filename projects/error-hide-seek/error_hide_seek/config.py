from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    sync_database_url: str
    anthropic_api_key: str
    corpus_size: int = 200
    api_port: int = 8004
    allowed_origins: str = "http://localhost:5174"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore[call-arg]
