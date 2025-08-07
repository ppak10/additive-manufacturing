import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated


def register_workspace_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def workspace_initialize(
        workspace_name: str,
        out_path: Path | None = None,
        force: Annotated[
            bool, typer.Option("--force", help="Overwrite existing workspace")
        ] = False,
    ) -> None:
        """Create a folder to store data related to a workspace."""
        from am.workspace import Workspace

        try:
            workspace = Workspace(
                name=workspace_name,
                out_path=out_path,
            )
            workspace_config = workspace.create_workspace(out_path, force)
            rprint(f"✅ Workspace initialized at: {workspace_config.workspace_path}")
        except:
            rprint("⚠️  [yellow]Unable to create workspace directory[/yellow]")
            _ = typer.Exit()

    _ = app.command(name="init")(workspace_initialize)

    return workspace_initialize
