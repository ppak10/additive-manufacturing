from mcp.server.fastmcp import FastMCP

def register_tools(app: FastMCP):

    @app.tool(
        title="add",
        description="tool for adding two numbers together"
    )
    def add(a: int, b: int) -> int:
        print("adding...")
        return a + b
    
