import typer

from pathlib import Path
from typing_extensions import Annotated, cast


def register_workspace_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def workspace_initialize(
        name: str,
        out_path: Path | None = None,
        force: Annotated[
            bool, typer.Option("--force", help="Overwrite existing workspace")
        ] = False,
        include_examples: Annotated[
            bool,
            typer.Option("--include-examples", help="Copy examples parts"),
        ] = False,
    ) -> None:
        """
        Initialize additive manufacturing workspace folder with subfolders.
        """
        from rich import print as rprint

        from wa.workspace.tools.create import create_workspace
        from am.workspace import initialize_configs, initialize_parts

        try:
            workspace = create_workspace(name, out_path, force)
            workspace_path = cast(Path, workspace.workspace_path)

            initialize_configs(workspace_path)
            initialize_parts(workspace_path, include_examples)
            rprint(f"✅ Workspace initialized at `{workspace_path}`")

        except FileNotFoundError as e:
            rprint(f"⚠️  [yellow]{e}[/yellow]")
            raise typer.Exit(code=1)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize workspace: {e}[/yellow]")
            raise typer.Exit(code=1)

    return workspace_initialize
