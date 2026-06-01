from __future__ import annotations

from pydantic_settings import BaseSettings  # type: ignore[import-untyped]


class Settings(BaseSettings):
    api_url: str = "http://localhost:8000"
    actor_id: str = "ai-reviewer"
    actor_role: str = "senior_reviewer"

    # LLM backend
    backend: str = "ollama"  # "claude" or "ollama"
    claude_model: str = "claude-haiku-4-5-20251001"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "gemma2:9b"

    # Behaviour
    confidence_threshold: float = 0.80
    poll_interval: int = 30  # seconds
    batch_size: int = 10     # cases per poll cycle

    # Claude cost guardrails
    # Haiku-4-5 pricing: $0.80/MTok input, $4.00/MTok output
    # Estimated ~500 input + 100 output tokens per case
    claude_cost_per_case_usd: float = 0.0008
    claude_max_cases: int = 10  # hard cap; 0 = unlimited (dangerous)

    model_config = {"env_file": ".env", "env_prefix": "REVIEWER_", "extra": "ignore"}


settings = Settings()
