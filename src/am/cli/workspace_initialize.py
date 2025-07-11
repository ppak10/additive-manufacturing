import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli import VerboseOption
from am.workspace import Workspace

def register_workspace_initialize(app):
    @app.command(name="initialize")
    def workspace_initialize(
            workspace_name: str,
            verbose: VerboseOption | None = None,
            out_path: Path | None = None,
            force: Annotated[
                bool,
                typer.Option(
                    "--force",
                    help="Overwrite existing workspace"
                )
            ] = False
        ) -> None:
        """Create a folder to store data related to a workspace."""

        try:
            workspace = Workspace(name=workspace_name, verbose=verbose, out_path=out_path)
            workspace_path = workspace.create_workspace(out_path, force)
            rprint(f"✅ Workspace initialized at: {workspace_path}")
        except:
            rprint("⚠️  [yellow]Unable to create workspace directory[/yellow]")
            typer.Exit()

    app.command(name="init")(workspace_initialize)

    return workspace_initialize

