from mcp.server.fastmcp import FastMCP

from am.workspace.mcp import register_workspace
from am.segmenter.mcp import register_segmenter
from am.mcp.resources import register_resources

app = FastMCP(name="additive-manufacturing")

_ = register_resources(app)
_ = register_segmenter(app)
_ = register_workspace(app)

def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()
