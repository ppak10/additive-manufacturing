import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption, WorkspaceOption


def register_segmenter_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def segmenter_initialize(
        verbose: VerboseOption | None = False,
        workspace: WorkspaceOption | None = None,
        include_examples: Annotated[
            bool,
            typer.Option("--include_examples", help="Copy over examples from package"),
        ] = True,
    ) -> None:
        """Create folder for segmenter data inside workspace folder."""
        from am.segmenter import Segmenter

        if workspace is not None:
            # Get workspace path from name.
            from am.workspace import WorkspaceConfig
            project_root = WorkspaceConfig.get_project_root_from_package()
            workspace_dir = project_root / "out" / workspace

        else:
            # Check for workspace config file in current directory
            workspace_dir = Path.cwd()

        config_file = workspace_dir / "config.json"

        if not config_file.exists():
            rprint(
                f"❌ [red]This is not a valid workspace folder. `{config_file}` not found.[/red]"
            )
            raise typer.Exit(code=1)

        try:
            segmenter = Segmenter()
            segmenter.initialize(
                segmenter_path=workspace_dir / "segmenter", include_examples=include_examples
            )
            rprint(f"✅ Segmenter initialized")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init")(segmenter_initialize)
    return segmenter_initialize
