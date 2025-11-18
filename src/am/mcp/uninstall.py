import subprocess

from rich import print as rprint


def uninstall(client: str) -> None:
    cmd = None
    match client:
        case "claude-code":
            cmd = ["claude", "mcp", "remove", "additive-manufacturing"]

        case "gemini-cli":
            cmd = ["gemini", "mcp", "remove", "additive-manufacturing"]

        case "codex":
            cmd = ["codex", "mcp", "remove", "additive-manufacturing"]

        case _:
            rprint("[yellow]No client provided.[/yellow]\n")

    if cmd is not None:
        try:
            rprint(f"[blue]Running command:[/blue] {' '.join(cmd)}")
            subprocess.run(cmd, check=True)

        except subprocess.CalledProcessError as e:
            rprint(f"[red]Command failed with return code {e.returncode}[/red]")
            rprint(f"[red]Error output: {e.stderr}[/red]" if e.stderr else "")
        except Exception as e:
            rprint(f"[red]Unexpected error running command:[/red] {e}")
