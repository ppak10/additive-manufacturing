from mcp.server.fastmcp import FastMCP

from am.mcp.resources import register_resources
from am.mcp.tools import register_tools
from am.mcp.workspace import register_workspace

app = FastMCP(name="additive-manufacturing")

_ = register_resources(app)
_ = register_tools(app)
_ = register_workspace(app)

