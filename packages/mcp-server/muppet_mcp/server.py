from mcp.server.fastmcp import FastMCP

from muppet_mcp.tools.manifest import get_workspace_manifest
from muppet_mcp.tools.role import load_role_context, transition_role
from muppet_mcp.tools.files import read_monorepo_file, atomic_write_feature
from muppet_mcp.tools.state import update_agent_state

mcp = FastMCP(
    "muppet-labs",
    instructions=(
        "ICM-aware workspace runtime for the muppet-labs monorepo. "
        "Use get_workspace_manifest to orient at session start. "
        "Use load_role_context before executing any role. "
        "Use transition_role to hand off between roles — it archives the current output atomically. "
        "Use update_agent_state to write decisions or session summaries to project-state.md. "
        "Use read_monorepo_file for any file read; use atomic_write_feature for multi-file writes."
    ),
)

mcp.tool()(get_workspace_manifest)
mcp.tool()(load_role_context)
mcp.tool()(transition_role)
mcp.tool()(read_monorepo_file)
mcp.tool()(atomic_write_feature)
mcp.tool()(update_agent_state)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
