from mcp.server.fastmcp import FastMCP

def register_resources(app: FastMCP):
    @app.resource("resource://templates")
    def resource_templates() -> list[str]:
        """
        Exposes endpoints for resource templates since it seems that they
        are not automatically detected by clients like claude code
        """
        return [ "workspace://{workspace}/parts" ]

    return resource_templates


