import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated


def register_workspace_list(app: typer.Typer):
    @app.command(name="list")
    def workspace_list() -> None:
        """List created workspaces."""

        from am.workspace import Workspace
        workspace_names =Workspace.list_workspaces()

        try:
            if workspace_names is None:
                rprint("⚠️  [yellow]No workspaces found.[/yellow]")
            else:
                rprint("Workspaces:")
                for index, name in enumerate(workspace_names):
                    rprint(f"{index + 1}. [cyan]{name}[/cyan]")
        except:
            rprint("⚠️  [yellow]Unable to list workspaces[/yellow]")
            _ = typer.Exit()

    _ = app.command(name="ls")(workspace_list)

    return workspace_list
