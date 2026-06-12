import re
import shutil
from datetime import date

import muppet_mcp.config as cfg
from muppet_mcp.telemetry import log_event


def load_role_context(role_name: str) -> str:
    """Return a role's CONTEXT.md plus the resource files listed in its Inputs table."""
    role_dir = cfg.WORKSPACE_ROOT / "roles" / role_name
    context_path = role_dir / "CONTEXT.md"

    if not context_path.exists():
        available = [
            p.name for p in (cfg.WORKSPACE_ROOT / "roles").iterdir() if p.is_dir()
        ]
        return f"ERROR: Role '{role_name}' not found. Available: {', '.join(sorted(available))}"

    context = context_path.read_text()
    parts: list[str] = [f"=== roles/{role_name}/CONTEXT.md ===\n{context}"]

    for resource_path in _parse_resource_inputs(context):
        full_path = cfg.WORKSPACE_ROOT / resource_path
        if full_path.exists():
            parts.append(f"\n=== {resource_path} ===\n{full_path.read_text()}")
        else:
            parts.append(
                f"\n=== {resource_path} ===\n[NOTE: file contains a pattern placeholder — specify language before loading, e.g. resources/python-conventions.md]"
            )

    output_path = role_dir / "output" / "output.md"
    if output_path.exists():
        parts.append(
            f"\n=== roles/{role_name}/output/output.md (existing — resuming?) ===\n{output_path.read_text()}"
        )

    return "\n".join(parts)


def transition_role(from_role: str, to_role: str, project_name: str) -> str:
    """
    Archive the current role's output, then return the next role's full context.
    Enforces the archiving rule and the one-role-at-a-time gate from routing.md.
    """
    from_dir = cfg.WORKSPACE_ROOT / "roles" / from_role
    output_path = from_dir / "output" / "output.md"

    if not output_path.exists():
        return (
            f"ERROR: roles/{from_role}/output/output.md does not exist. "
            f"The {from_role} role must write its output before transitioning to {to_role}."
        )

    archive_dir = from_dir / "archive"
    archive_dir.mkdir(exist_ok=True)
    archive_name = f"{date.today().isoformat()}-{project_name}-output.md"
    archive_path = archive_dir / archive_name
    shutil.copy2(output_path, archive_path)

    log_event(
        tool="transition_role",
        action="archive",
        files_affected=[str(archive_path.relative_to(cfg.WORKSPACE_ROOT))],
        from_role=from_role,
        to_role=to_role,
        project=project_name,
    )

    result = load_role_context(to_role)
    return f"✓ Archived roles/{from_role}/output/output.md → roles/{from_role}/archive/{archive_name}\n\n{result}"


def _parse_resource_inputs(context: str) -> list[str]:
    """Extract resource file paths from the Inputs table in a role CONTEXT.md."""
    paths: list[str] = []
    for line in context.splitlines():
        # Match table rows where first column is Resources or Skills
        if not re.match(r"\|\s*(Resources|Skills)\s*\|", line):
            continue
        # Extract backtick-quoted path from second column
        m = re.search(r"`(resources/[^`]+|skills/[^`]+)`", line)
        if m:
            paths.append(m.group(1))
    return paths
