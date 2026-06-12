import re
from typing import Literal

from muppet_mcp.config import WORKSPACE_ROOT
from muppet_mcp.telemetry import log_event

STATE_PATH = WORKSPACE_ROOT / "_config" / "project-state.md"

_DECISION_HEADER = "| Date | Decision | Reason |"
_DECISION_SEP = "|------|----------|--------|"


def update_agent_state(
    type: Literal["decision", "session_summary", "active_project"],
    date_str: str,
    content: str,
    reason: str = "",
    stopped_at: str = "",
    project_name: str = "",
    status: str = "",
    sequence_position: str = "",
) -> str:
    """
    Validated write to _config/project-state.md.

    type="decision":         date_str + content (decision text) + reason required.
    type="session_summary":  date_str + content (summary text) + stopped_at required.
    type="active_project":   project_name + status + sequence_position required.
    """
    if not STATE_PATH.exists():
        return f"ERROR: project-state.md not found at {STATE_PATH}"

    text = STATE_PATH.read_text()

    if type == "decision":
        if not date_str or not content or not reason:
            return "ERROR: decision requires date_str, content (decision text), and reason."
        updated = _insert_decision(text, date_str, content, reason)

    elif type == "session_summary":
        if not date_str or not content or not stopped_at:
            return "ERROR: session_summary requires date_str, content, and stopped_at."
        updated = _prepend_session_summary(text, date_str, content, stopped_at)

    elif type == "active_project":
        if not project_name or not status or not sequence_position:
            return "ERROR: active_project requires project_name, status, and sequence_position."
        updated = _update_active_project(text, project_name, status, sequence_position)

    else:
        return f"ERROR: Unknown type '{type}'. Must be decision, session_summary, or active_project."

    if updated == text:
        return "ERROR: Could not locate the target section in project-state.md. File may have drifted from expected format."

    STATE_PATH.write_text(updated)
    log_event(
        tool="update_agent_state",
        action=type,
        files_affected=["_config/project-state.md"],
        project=project_name or "—",
    )
    return f"✓ project-state.md updated ({type})"


def _insert_decision(text: str, date_str: str, decision: str, reason: str) -> str:
    marker = f"{_DECISION_HEADER}\n{_DECISION_SEP}"
    new_row = f"| {date_str} | {decision} | {reason} |"
    return text.replace(marker, f"{marker}\n{new_row}", 1)


def _prepend_session_summary(
    text: str, date_str: str, summary: str, stopped_at: str
) -> str:
    header = "## Last Session Summary"
    idx = text.find(header)
    if idx == -1:
        return text

    # Find the end of the header line and insert new block right after
    after_header = text.find("\n", idx) + 1
    new_block = (
        f"\n**Date:** {date_str}\n"
        f"**What was completed this session:**\n{summary}\n\n"
        f"**Where we stopped:** {stopped_at}\n\n---\n"
    )
    return text[:after_header] + new_block + text[after_header:]


def _update_active_project(
    text: str, project_name: str, status: str, sequence_position: str
) -> str:
    # Replace everything between ## Active Project and the next --- separator
    pattern = r"(## Active Project\n)(.*?)(\n---)"
    replacement = (
        f"\\1\n**Name:** {project_name}\n"
        f"**Status:** {status}\n"
        f"**Sequence position:** {sequence_position}\n"
        "\\3"
    )
    updated = re.sub(pattern, replacement, text, count=1, flags=re.DOTALL)
    return updated
