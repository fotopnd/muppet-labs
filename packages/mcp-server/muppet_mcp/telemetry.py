import json
from datetime import datetime, timezone
from typing import Any

import muppet_mcp.config as cfg


def log_event(tool: str, action: str, files_affected: list[str], **extra: Any) -> None:
    cfg.TELEMETRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "action": action,
        "files_affected": files_affected,
        **extra,
    }

    entries: list[dict] = []
    if cfg.TELEMETRY_PATH.exists():
        try:
            entries = json.loads(cfg.TELEMETRY_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append(entry)
    cfg.TELEMETRY_PATH.write_text(json.dumps(entries, indent=2))
