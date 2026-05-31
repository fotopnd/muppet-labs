from __future__ import annotations

import os
from pathlib import Path

import yaml

from eval.models import ModelBackend, RunConfig

DEFAULT_DB_PATH = Path("eval_results.db")
DEFAULT_RUBRICS_DIR = Path(__file__).parent.parent / "rubrics"
DEFAULT_CASES_DIR = Path(__file__).parent.parent / "test_cases"
DEFAULT_MODELS_FILE = Path("models.yaml")
DEFAULT_LOCAL_URL = "http://localhost:11434/v1"
DEFAULT_MLX_URL = "http://localhost:8080/v1"


def load_run_config(config_path: Path) -> RunConfig:
    with config_path.open() as f:
        data = yaml.safe_load(f)
    return RunConfig.model_validate(data)


def load_model_aliases(path: Path | None = None) -> dict[str, dict]:
    """Load alias definitions from models.yaml. Returns {} if file is missing."""
    p = path or DEFAULT_MODELS_FILE
    if not p.exists():
        return {}
    with p.open() as f:
        data = yaml.safe_load(f) or {}
    raw = data.get("aliases", {})
    result = {}
    for alias, value in raw.items():
        if isinstance(value, str):
            result[alias] = {"model": value}
        else:
            result[alias] = value
    return result


def resolve_alias(name: str, aliases: dict[str, dict]) -> tuple[str, str | None]:
    """Return (resolved_model_name, backend_override_or_None)."""
    if name in aliases:
        entry = aliases[name]
        return entry["model"], entry.get("backend")
    return name, None


def resolve_db_path(override: Path | None) -> Path:
    if override:
        return override
    env = os.environ.get("EVAL_DB_PATH")
    return Path(env) if env else DEFAULT_DB_PATH


def resolve_anthropic_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise OSError(
            "ANTHROPIC_API_KEY is not set. Export it or use --no-judge to skip LLM scoring."
        )
    return key


def resolve_local_url(config: RunConfig) -> str:
    if config.endpoint_url:
        return config.endpoint_url
    if config.model_backend == ModelBackend.MLX:
        return os.environ.get("EVAL_MLX_URL", DEFAULT_MLX_URL)
    return os.environ.get("EVAL_LOCAL_URL", DEFAULT_LOCAL_URL)
