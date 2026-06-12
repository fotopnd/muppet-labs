import os
import tempfile
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel

import muppet_mcp.config as cfg
from muppet_mcp.telemetry import log_event

MAX_BYTES_DEFAULT = 51_200  # 50 KB


class FileSpec(BaseModel):
    path: str
    content: str


def read_monorepo_file(
    path: str,
    max_bytes: Annotated[int, "Maximum file size in bytes"] = MAX_BYTES_DEFAULT,
) -> str:
    """Read a file under cfg.WORKSPACE_ROOT with size and traversal guards."""
    resolved = _safe_resolve(path)
    if resolved is None:
        return f"ERROR: Path '{path}' is outside cfg.WORKSPACE_ROOT ({cfg.WORKSPACE_ROOT}). Directory traversal rejected."

    if not resolved.exists():
        return f"ERROR: File not found: {path}"
    if not resolved.is_file():
        return f"ERROR: '{path}' is a directory, not a file."

    size = resolved.stat().st_size
    if size > max_bytes:
        return (
            f"ERROR: File too large ({size:,} bytes > {max_bytes:,} byte limit). "
            f"This guard prevents token overflow. Use a higher max_bytes or read a subsection."
        )

    raw = resolved.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return f"ERROR: '{path}' appears to be a binary file and cannot be returned as text."


def atomic_write_feature(files: list[FileSpec], manifest_note: str) -> str:
    """
    Write multiple files atomically (write-to-temp then rename) and log to telemetry.
    All paths must be within cfg.WORKSPACE_ROOT.
    """
    resolved: list[tuple[Path, str]] = []
    for spec in files:
        r = _safe_resolve(spec.path)
        if r is None:
            return f"ERROR: Path '{spec.path}' is outside cfg.WORKSPACE_ROOT. Operation aborted — no files written."
        resolved.append((r, spec.content))

    temp_files: list[tuple[Path, Path]] = []
    try:
        for target, content in resolved:
            target.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_path = tempfile.mkstemp(dir=target.parent, prefix=".mcp-tmp-")
            os.close(fd)
            tmp = Path(tmp_path)
            tmp.write_text(content, encoding="utf-8")
            temp_files.append((tmp, target))

        # All writes succeeded — rename atomically
        for tmp, target in temp_files:
            tmp.replace(target)

    except Exception as exc:
        # Clean up any temp files on failure
        for tmp, _ in temp_files:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
        return f"ERROR: Write failed: {exc}. No files were written."

    written = [str(t.relative_to(cfg.WORKSPACE_ROOT)) for _, t in temp_files]
    log_event(
        tool="atomic_write_feature",
        action="write",
        files_affected=written,
        manifest_note=manifest_note,
    )

    return f"✓ Written ({len(written)} files):\n" + "\n".join(
        f"  - {p}" for p in written
    )


def _safe_resolve(path: str) -> Path | None:
    candidate = (cfg.WORKSPACE_ROOT / path).resolve()
    try:
        candidate.relative_to(cfg.WORKSPACE_ROOT)
    except ValueError:
        return None
    return candidate
