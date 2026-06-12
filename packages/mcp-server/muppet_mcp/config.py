import os
from pathlib import Path

WORKSPACE_ROOT: Path = Path(
    os.environ.get("WORKSPACE_ROOT", Path.home() / "Documents" / "muppet-labs")
).resolve()

TELEMETRY_PATH = WORKSPACE_ROOT / ".mcp" / "telemetry.json"

NOISE_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "dist",
        "build",
        ".next",
        ".turbo",
        "archive",
    }
)

NOISE_RESOURCE_SUBDIRS = frozenset({"models", "datasets", "evals"})
