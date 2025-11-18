import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated


def register_workspace_create(app: typer.Typer):
    @app.command(name="create")
    def workspace_create(
        workspace_name: str,
        workspaces_path: Path | None = None,
        force: Annotated[
            bool, typer.Option("--force", help="Overwrite existing subfolder")
        ] = False,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples", help="Copy examples parts"),
        ] = False,
    ) -> None:
        """Create a folder to store data related to a workspace."""
        from am.workspace.create import create_additive_manufacturing_workspace

        try:
            workspace = create_additive_manufacturing_workspace(
                workspace_name=workspace_name,
                workspaces_path=workspaces_path,
                force=force,
                include_examples=include_examples,
            )
            rprint(f"✅ Workspace created at: {workspace.path}")
        except FileExistsError as e:
            rprint(f"⚠️  [yellow]Workspace: `{workspace_name}` already exists.[/yellow]")
            rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
            _ = typer.Exit()
        except:
            rprint("⚠️  [yellow]Unable to create workspace directory[/yellow]")
            _ = typer.Exit()

    return workspace_create
