from mcp.server.fastmcp import FastMCP

def register_resources(app: FastMCP):
    @app.resource("docs://search")
    def search() -> str:
        print("searching...")
        return "searching..."

    return search


