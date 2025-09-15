import shutil
import subprocess

from importlib.resources import files
from pathlib import Path
from rich import print as rprint

from am import data


def install(path: Path, client: str, include_agent: bool = True) -> None:
    match client:
        case "claude-code":
            # TODO: Handle case if agent already exists
            # (i.e. auto remove existing agent if updating.)
            try:
                claude_cmd = [
                    "claude",
                    "mcp",
                    "add-json",
                    "am",
                    f'{{"command": "uv", "args": ["--directory", "{path}", "run", "-m", "am.mcp"]}}',
                ]

                rprint(f"[blue]Running command:[/blue] {' '.join(claude_cmd)}")
                subprocess.run(claude_cmd, check=True)

                if include_agent:
                    # Copies premade agent configuration to `.claude/agents`
                    agent_file = files(data) / "mcp" / "agent.md"
                    claude_agents_path = path / ".claude" / "agents"
                    claude_agents_path.mkdir(parents=True, exist_ok=True)
                    claude_agent_config_path = claude_agents_path / "am.md"
                    with (
                        agent_file.open("rb") as src,
                        open(claude_agent_config_path, "wb") as dst,
                    ):
                        shutil.copyfileobj(src, dst)
                    rprint(
                        f"[bold green]Installed agent under path:[/bold green] {claude_agent_config_path}"
                    )

            except subprocess.CalledProcessError as e:
                rprint(f"[red]Command failed with return code {e.returncode}[/red]")
                rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
            except Exception as e:
                rprint(f"[red]Unexpected error running command:[/red] {e}")

        case _:
            rprint(
                "[yellow]No client provided.[/yellow]\n"
                "[bold]Please specify where to install with one of the following:[/bold]\n"
                "  • [green]--client claude-code[/green] to install for Claude Code\n"
                "  • Other options coming soon..."
            )
