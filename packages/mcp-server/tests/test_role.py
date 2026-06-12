import pytest
from pathlib import Path
from unittest.mock import patch

import muppet_mcp.config as cfg


@pytest.fixture()
def workspace(tmp_path: Path):
    with patch.object(cfg, "WORKSPACE_ROOT", tmp_path):
        with patch.object(cfg, "TELEMETRY_PATH", tmp_path / ".mcp" / "telemetry.json"):
            yield tmp_path


def _make_role(
    workspace: Path, role_name: str, context: str, output: str | None = None
) -> None:
    role_dir = workspace / "roles" / role_name
    (role_dir / "output").mkdir(parents=True)
    (role_dir / "CONTEXT.md").write_text(context)
    if output is not None:
        (role_dir / "output" / "output.md").write_text(output)


_BRIEF_CONTEXT = """\
## Identity
Brief role.

## Inputs

| Source | File | Notes |
|--------|------|-------|
| Resources | `resources/vibecoding-style.md` | Style guide |
"""


def test_load_role_context_returns_context_and_resources(workspace: Path) -> None:
    from muppet_mcp.tools.role import load_role_context

    _make_role(workspace, "brief", _BRIEF_CONTEXT)
    (workspace / "resources").mkdir()
    (workspace / "resources" / "vibecoding-style.md").write_text("vibe content")

    result = load_role_context("brief")
    assert "=== roles/brief/CONTEXT.md ===" in result
    assert "Brief role." in result
    assert "=== resources/vibecoding-style.md ===" in result
    assert "vibe content" in result


def test_load_role_context_unknown_role_returns_error(workspace: Path) -> None:
    from muppet_mcp.tools.role import load_role_context

    (workspace / "roles").mkdir()
    result = load_role_context("nonexistent")
    assert result.startswith("ERROR:")


def test_load_role_context_includes_existing_output(workspace: Path) -> None:
    from muppet_mcp.tools.role import load_role_context

    _make_role(workspace, "brief", _BRIEF_CONTEXT, output="prior output content")
    (workspace / "resources").mkdir()
    result = load_role_context("brief")
    assert "prior output content" in result
    assert "resuming" in result


def test_transition_role_archives_and_returns_next_context(workspace: Path) -> None:
    from muppet_mcp.tools.role import transition_role

    _make_role(workspace, "brief", "brief context", output="brief output")
    _make_role(workspace, "planner", "planner context")

    result = transition_role("brief", "planner", "my-project")
    assert "✓ Archived" in result
    archive_dir = workspace / "roles" / "brief" / "archive"
    archived = list(archive_dir.glob("*my-project-output.md"))
    assert len(archived) == 1
    assert archived[0].read_text() == "brief output"
    assert "planner context" in result


def test_transition_role_no_output_returns_error(workspace: Path) -> None:
    from muppet_mcp.tools.role import transition_role

    _make_role(workspace, "brief", "brief context")  # no output.md
    _make_role(workspace, "planner", "planner context")

    result = transition_role("brief", "planner", "my-project")
    assert result.startswith("ERROR:")
    assert "output" in result.lower()
