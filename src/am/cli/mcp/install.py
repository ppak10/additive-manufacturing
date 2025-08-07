import subprocess
import typer

from typing_extensions import Annotated

from pathlib import Path
from rich import print as rprint

def register_mcp_install(app: typer.Typer):
    @app.command(name="install")
    def mcp_development(
        claude_code: Annotated[bool, typer.Option("--claude-code")] = False,
        project_path: Annotated[str | None, typer.Option("--project-path")] = None,
    ) -> None:
        import am

        if project_path: 
            am_path = Path(project_path)
        else:
            # Path(am.__file__) Should be something like this when installed
            # "/mnt/am/GitHub/additive-manufacturing-agent/.venv/lib/python3.13/site-packages/am"
            # Path(am.__file__).parents[4] should be the project root
            # "/mnt/am/GitHub/additive-manufacturing-agent/"
            am_path = Path(am.__file__).parents[4]

        rprint(f"[bold green]Using `additive-manufacturing` packaged under project path:[/bold green] {am_path}")

        if claude_code:
            try:
                claude_cmd = [
                    "claude", "mcp", "add-json", "am",
                    f'{{"command": "uv", "args": ["--directory", "{am_path}", "run", "-m", "am.mcp"]}}'
                ]
            
                rprint(f"[blue]Running command:[/blue] {' '.join(claude_cmd)}")
                subprocess.run(claude_cmd, check=True)
            
            except subprocess.CalledProcessError as e:
                rprint(f"[red]Command failed with return code {e.returncode}[/red]")
                rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
            except Exception as e:
                rprint(f"[red]Unexpected error running command:[/red] {e}")

        else:
            rprint(
                "[yellow]No client provided.[/yellow]\n"
                "[bold]Please specify where to install with one of the following:[/bold]\n"
                "  • [green]--claude-code[/green] to install for Claude Code\n"
                "  • Other options coming soon..."
            )
        

    _ = app.command(name="install")(mcp_development)
    return mcp_development

