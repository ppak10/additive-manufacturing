import json
import shutil
import subprocess
import sys

from importlib.resources import files
from pathlib import Path
from rich import print as rprint

from am import data
from wa.mcp.install import install as install_wa


def install(path: Path, client: str, include_agent: bool = True) -> None:
    match client:
        case "claude-code":
            claude_wa_check = ["claude", "mcp", "get", "workspace"]
            rprint(f"[blue]Running command:[/blue] {' '.join(claude_wa_check)}")
            result = subprocess.run(
                claude_wa_check, capture_output=True, text=True, check=False
            )

            if result.returncode != 0:
                rprint(
                    "[yellow]No existing MCP server found for 'workspace-agent'. Installing...[/yellow]"
                )
                install_wa(path=path, client=client, include_agent=include_agent)

            cmd = [
                "claude",
                "mcp",
                "add-json",
                "additive-manufacturing",
                f'{{"command": "uv", "args": ["--directory", "{path}", "run", "-m", "am.mcp"]}}',
            ]

            if include_agent:
                # Copies premade agent configuration to `.claude/agents`
                agent_file = files(data) / "mcp" / "agent.md"
                claude_agents_path = path / ".claude" / "agents"
                claude_agents_path.mkdir(parents=True, exist_ok=True)
                claude_agent_config_path = (
                    claude_agents_path / "additive-manufacturing.md"
                )
                with (
                    agent_file.open("rb") as src,
                    open(claude_agent_config_path, "wb") as dst,
                ):
                    shutil.copyfileobj(src, dst)
                rprint(
                    f"[bold green]Installed agent under path:[/bold green] {claude_agent_config_path}"
                )

        case "claude-desktop":
            # Determine config file path based on platform
            if sys.platform == "darwin":
                config_path = (
                    Path.home()
                    / "Library"
                    / "Application Support"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
            elif sys.platform == "win32":
                config_path = (
                    Path.home()
                    / "AppData"
                    / "Roaming"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
            else:  # Linux
                config_path = (
                    Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
                )

            # Ensure config directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Read existing config or create new one
            if config_path.exists():
                with open(config_path, "r") as f:
                    config = json.load(f)
                rprint(f"[blue]Found existing config at:[/blue] {config_path}")
            else:
                config = {}
                rprint(f"[yellow]Creating new config at:[/yellow] {config_path}")

            # Ensure mcpServers section exists
            if "mcpServers" not in config:
                config["mcpServers"] = {}

            # Add workspace server if not present
            if "workspace" not in config["mcpServers"]:
                rprint("[yellow]Adding 'workspace' MCP server to config...[/yellow]")
                config["mcpServers"]["workspace"] = {
                    "command": "uv",
                    "args": ["--directory", str(path), "run", "-m", "wa.mcp"],
                }

            # Add additive-manufacturing server
            rprint(
                "[blue]Adding 'additive-manufacturing' MCP server to config...[/blue]"
            )
            config["mcpServers"]["additive-manufacturing"] = {
                "command": "uv",
                "args": ["--directory", str(path), "run", "-m", "am.mcp"],
            }

            # Write config back
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            rprint(
                f"[bold green]Successfully updated config at:[/bold green] {config_path}"
            )
            rprint(
                "[yellow]Note: Please restart Claude Desktop for changes to take effect.[/yellow]"
            )

            # Skip agent installation as Claude Desktop doesn't support custom agents
            if include_agent:
                rprint(
                    "[yellow]Note: Claude Desktop does not support custom agents like Claude Code does.[/yellow]"
                )

            return  # Early return since we don't need to run subprocess command

        case "gemini-cli":
            gemini_wa_check = ["gemini", "mcp", "list"]
            rprint(f"[blue]Running command:[/blue] {' '.join(gemini_wa_check)}")
            result = subprocess.run(
                gemini_wa_check, capture_output=True, text=True, check=False
            )

            if result.stdout == "No MCP servers configured.\n":
                rprint(
                    "[yellow]No existing MCP server found for 'workspace-agent'. Installing...[/yellow]"
                )
                install_wa(path=path, client=client, include_agent=include_agent)

            cmd = [
                "gemini",
                "mcp",
                "add",
                "additive-manufacturing",
                "uv",
                "--directory",
                f"{path}",
                "run",
                "-m",
                "am.mcp",
            ]

        case "codex":
            codex_wa_check = ["codex", "mcp", "get", "workspace"]
            rprint(f"[blue]Running command:[/blue] {' '.join(codex_wa_check)}")
            result = subprocess.run(
                codex_wa_check, capture_output=True, text=True, check=False
            )

            if result.stdout == "No MCP servers configured.\n":
                rprint(
                    "[yellow]No existing MCP server found for 'workspace-agent'. Installing...[/yellow]"
                )
                install_wa(path=path, client=client, include_agent=include_agent)

            cmd = [
                "codex",
                "mcp",
                "add",
                "additive-manufacturing",
                "uv",
                "--directory",
                f"{path}",
                "run",
                "-m",
                "am.mcp",
            ]

        case _:
            rprint("[yellow]No client provided.[/yellow]")

    try:
        rprint(f"[blue]Running command:[/blue] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Command failed with return code {e.returncode}[/red]")
        rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
    except Exception as e:
        rprint(f"[red]Unexpected error running command:[/red] {e}")
