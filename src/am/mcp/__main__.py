from mcp.server.fastmcp import FastMCP

from am.mcp.workspace import register_workspace

app = FastMCP(name="additive-manufacturing")

_ = register_workspace(app)

