import os
import subprocess
import sys
import typer

from importlib.resources import files
from rich import print as rprint


def register_mcp_development(app: typer.Typer):
    @app.command(name="development")
    def mcp_development() -> None:
        from mcp.cli import cli

        # try:
        rprint(f"Starting MCP Development Server")

        # Get the correct npx command
        npx_cmd = cli._get_npx_command()

        if not npx_cmd:
            cli.logger.error(
                "npx not found. Please ensure Node.js and npm are properly installed and added to your system PATH."
            )
            raise typer.Exit(1)

        # Run the MCP Inspector command with shell=True on Windows
        shell = sys.platform == "win32"

        file_spec = files("am.mcp").joinpath("__main__.py")

        print(file_spec)

        uv_cmd = ["uv", "run", "--with", "mcp", "mcp", "run", str(file_spec)]
        print(f"uv_cmd: {uv_cmd}")

        process = subprocess.run(
            [npx_cmd, "@modelcontextprotocol/inspector"] + uv_cmd,
            check=True,
            shell=shell,
            env=dict(os.environ.items()),  # Convert to list of tuples for env update
        )
        _ = typer.Exit(process.returncode)
        rprint(f"✅  MCP Development Running")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="dev")(mcp_development)
    return mcp_development
