from mcp.server.fastmcp import FastMCP

from am.config.mcp import register_config

from am.slicer.mcp import register_slicer_slice
from am.simulator.mcp import register_simulator_tool_process_map
from am.workspace.mcp import register_workspace_create

app = FastMCP(name="additive-manufacturing")

_ = register_config(app)
_ = register_simulator_tool_process_map(app)
_ = register_slicer_slice(app)
_ = register_workspace_create(app)


def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()
