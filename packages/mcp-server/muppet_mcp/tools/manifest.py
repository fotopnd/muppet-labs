import re
from pathlib import Path

import muppet_mcp.config as cfg


def get_workspace_manifest() -> str:
    """Return a compressed ICM workspace state. Replaces the 5-file session-start read."""
    parts: list[str] = []

    parts.append("# Muppet-Labs Workspace Manifest\n")

    state_path = cfg.cfg.WORKSPACE_ROOT / "_config" / "project-state.md"
    if state_path.exists():
        parts.append(_parse_project_state(state_path.read_text()))
    else:
        parts.append("**project-state.md not found**\n")

    parts.append(_list_roles())
    parts.append(_workspace_tree())

    return "\n".join(parts)


def _parse_project_state(content: str) -> str:
    lines = content.splitlines()
    out: list[str] = ["## Active Project\n"]

    in_active = False
    in_parked = False
    active_lines: list[str] = []
    parked_names: list[str] = []

    for line in lines:
        if line.startswith("## Active Project"):
            in_active = True
            in_parked = False
            continue
        if line.startswith("## Parked Projects"):
            in_active = False
            in_parked = True
            continue
        if line.startswith("## ") and in_active:
            in_active = False
        if line.startswith("## ") and in_parked:
            in_parked = False

        if in_active and line.strip():
            active_lines.append(line)

        if in_parked:
            # Extract bold project name: **name:** at line start
            m = re.match(r"\*\*([^*]+)\*\*", line)
            if m:
                parked_names.append(m.group(1).rstrip(":"))

    out.extend(
        active_lines[:12]
    )  # cap to avoid bloat from long sequence position lines
    out.append("")
    if parked_names:
        out.append("## Parked Projects\n")
        for name in parked_names:
            out.append(f"- {name}")
        out.append("")

    return "\n".join(out)


def _list_roles() -> str:
    roles_dir = cfg.WORKSPACE_ROOT / "roles"
    if not roles_dir.exists():
        return ""
    roles = sorted(
        p.name for p in roles_dir.iterdir() if p.is_dir() and not p.name.startswith(".")
    )
    return "## Available Roles\n\n" + ", ".join(f"`{r}`" for r in roles) + "\n"


def _workspace_tree() -> str:
    lines: list[str] = ["\n## Workspace Tree (noise-filtered)\n```"]
    _walk(cfg.WORKSPACE_ROOT, lines, prefix="", depth=0, max_depth=2)
    lines.append("```")
    return "\n".join(lines)


def _walk(
    path: Path, lines: list[str], prefix: str, depth: int, max_depth: int
) -> None:
    if depth > max_depth:
        return

    try:
        children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return

    dirs = [c for c in children if c.is_dir() and not _skip_dir(c, path)]
    files = [c for c in children if c.is_file() and not c.name.startswith(".")]

    for d in dirs:
        lines.append(f"{prefix}{d.name}/")
        _walk(d, lines, prefix + "  ", depth + 1, max_depth)

    if depth == max_depth and dirs:
        return

    for f in files[:10]:  # cap files per directory
        lines.append(f"{prefix}{f.name}")
    if len(files) > 10:
        lines.append(f"{prefix}... ({len(files) - 10} more files)")


def _skip_dir(d: Path, parent: Path) -> bool:
    if d.name.startswith("."):
        return True
    if d.name in cfg.NOISE_DIRS:
        return True
    # Skip resources/{models,datasets,evals} subdirs
    if parent.name == "resources" and d.name in cfg.NOISE_RESOURCE_SUBDIRS:
        return True
    return False
