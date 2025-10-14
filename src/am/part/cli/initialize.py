import typer

from typing_extensions import Annotated

from wa.cli.options import WorkspaceOption


def register_part_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def part_initialize(
        workspace: WorkspaceOption = None,
        include_defaults: Annotated[
            bool,
            typer.Option(
                "--include-defaults", help="Copy default part files from data directory"
            ),
        ] = True,
    ) -> None:
        """
        Initialize parts folder within workspace.
        """
        from rich import print as rprint

        from wa.cli.utils import get_workspace_path
        from am.part.initialize import initialize_parts_folder

        workspace_path = get_workspace_path(workspace)

        try:
            parts_dir, copied_files = initialize_parts_folder(
                workspace_path, include_defaults
            )

            if copied_files is not None:
                if copied_files:
                    rprint(
                        f"✅ Parts folder initialized at `{parts_dir}` with default files:"
                    )
                    for filename in copied_files:
                        rprint(f"   - {filename}")
                else:
                    rprint(
                        f"✅ Parts folder initialized at `{parts_dir}` (no default files found)"
                    )
            else:
                rprint(f"✅ Parts folder initialized at `{parts_dir}`")

        except FileNotFoundError as e:
            rprint(f"⚠️  [yellow]{e}[/yellow]")
            raise typer.Exit(code=1)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize parts folder: {e}[/yellow]")
            raise typer.Exit(code=1)

    return part_initialize
