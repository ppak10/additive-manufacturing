from mcp.server.fastmcp import FastMCP

from am.workspace.mcp import (
    register_workspace_initialize,
    register_workspace_list,
)
from am.segmenter.mcp import (
    register_segmenter_parse,
    register_segmenter_shape_2d,
    register_segmenter_visualize_layer,
)
from am.solver.mcp import register_solver
from am.mcp.resources import register_resources

app = FastMCP(name="additive-manufacturing")

_ = register_resources(app)
_ = register_segmenter_parse(app)
_ = register_segmenter_shape_2d(app)
_ = register_segmenter_visualize_layer(app)
_ = register_solver(app)
_ = register_workspace_initialize(app)
_ = register_workspace_list(app)

def main():
    """Entry point for the direct execution server."""
    app.run()

if __name__ == "__main__":
    main()
