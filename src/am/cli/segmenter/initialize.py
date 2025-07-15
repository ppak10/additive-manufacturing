import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption
from am.workspace import WorkspaceConfig

def register_segmenter_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def segmenter_initialize(
        verbose: VerboseOption | None = False,
        force: Annotated[
            bool, typer.Option("--force", help="Overwrite existing segmenter")
        ] = False,
    ) -> None:
        """Create folder for segmenter data inside workspace folder."""

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
            raise typer.Exit(code=1)

        try:
            workspace_config = WorkspaceConfig.load(config_file)
            print(workspace_config)
            # TODO: Initialize segmenter here
            rprint(f"✅ Segmenter initialized")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create workspace directory: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init")(segmenter_initialize)
    return segmenter_initialize

