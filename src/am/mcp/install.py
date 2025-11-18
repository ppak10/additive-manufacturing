import shutil
import subprocess

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
            codex_wa_check = ["codex", "mcp", "get", "wa"]
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
            rprint(
                "[yellow]No client provided.[/yellow]\n"
                "[bold]Please specify where to install with one of the following:[/bold]\n"
                "  • [green]--client claude-code[/green] to install for Claude Code\n"
                "  • Other options coming soon..."
            )

    try:
        rprint(f"[blue]Running command:[/blue] {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        rprint(f"[red]Command failed with return code {e.returncode}[/red]")
        rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
    except Exception as e:
        rprint(f"[red]Unexpected error running command:[/red] {e}")
