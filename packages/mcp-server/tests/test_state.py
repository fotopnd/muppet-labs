import pytest
from pathlib import Path
from unittest.mock import patch

import muppet_mcp.config as cfg
import muppet_mcp.tools.state as state_mod


@pytest.fixture()
def workspace(tmp_path: Path):
    config_dir = tmp_path / "_config"
    config_dir.mkdir()
    with patch.object(cfg, "WORKSPACE_ROOT", tmp_path):
        with patch.object(cfg, "TELEMETRY_PATH", tmp_path / ".mcp" / "telemetry.json"):
            with patch.object(state_mod, "STATE_PATH", config_dir / "project-state.md"):
                yield tmp_path, config_dir / "project-state.md"


def _base_state() -> str:
    return """\
# project-state.md

## Active Project

**Name:** my-project
**Status:** IN PROGRESS

---

## Last Session Summary

**Date:** 2026-06-01
**What was completed:** initial setup

---

## Decisions Log

> Add entries newest-first.

| Date | Decision | Reason |
|------|----------|--------|
| 2026-06-01 | First decision | because reasons |
"""


def test_insert_decision(workspace) -> None:
    _, state_path = workspace
    state_path.write_text(_base_state())
    from muppet_mcp.tools.state import update_agent_state

    result = update_agent_state(
        type="decision",
        date_str="2026-06-12",
        content="New decision",
        reason="New reason",
    )
    assert result.startswith("✓")
    text = state_path.read_text()
    new_row = "| 2026-06-12 | New decision | New reason |"
    old_row = "| 2026-06-01 | First decision | because reasons |"
    assert new_row in text
    assert old_row in text
    # Newest-first: new row must appear before old row in the decisions log
    assert text.index(new_row) < text.index(old_row)


def test_prepend_session_summary(workspace) -> None:
    _, state_path = workspace
    state_path.write_text(_base_state())
    from muppet_mcp.tools.state import update_agent_state

    result = update_agent_state(
        type="session_summary",
        date_str="2026-06-12",
        content="- completed things",
        stopped_at="ready for next role",
    )
    assert result.startswith("✓")
    text = state_path.read_text()
    assert "**Date:** 2026-06-12" in text
    # New summary must appear before old summary
    assert text.index("2026-06-12") < text.index("2026-06-01")


def test_missing_required_fields_returns_error(workspace) -> None:
    _, state_path = workspace
    state_path.write_text(_base_state())
    from muppet_mcp.tools.state import update_agent_state

    result = update_agent_state(
        type="decision", date_str="2026-06-12", content="", reason=""
    )
    assert result.startswith("ERROR:")


def test_missing_state_file_returns_error(workspace) -> None:
    _, state_path = workspace
    # Don't create the file
    from muppet_mcp.tools.state import update_agent_state

    result = update_agent_state(
        type="decision", date_str="2026-06-12", content="x", reason="y"
    )
    assert result.startswith("ERROR:")
