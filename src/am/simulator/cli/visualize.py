import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_solver_visualize(app: typer.Typer):
    from am.solver.layer import SolverOutputFolder

    @app.command(name="visualize")
    def solver_visualize(
        run_name: Annotated[
            str | None,
            typer.Option(
                help="Run name used for saving to solver mesh folder, defaults to most recent run."
            ),
        ] = None,
        output_folder: Annotated[
            SolverOutputFolder,
            typer.Option(help="Select which output to visualize"),
        ] = SolverOutputFolder.meshes,
        frame_format: Annotated[
            str, typer.Option(help="File extension to save frames in")
        ] = "png",
        include_axis: Annotated[
            bool, typer.Option(help="Toggle for including labels, ticks, and spines")
        ] = True,
        transparent: Annotated[
            bool, typer.Option(help="Toggle for transparent background")
        ] = False,
        units: Annotated[str, typer.Option(help="Units for plotting segments")] = "mm",
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from wa.cli.utils import get_workspace_path
        from am.solver.layer import SolverLayer

        workspace_path = get_workspace_path(workspace)

        runs_folder = workspace_path / "meshes"
        if run_name is None:
            # Get list of subdirectories sorted by modification time (newest first)
            run_dirs = sorted(
                [d for d in runs_folder.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )

            if not run_dirs:
                raise FileNotFoundError(f"❌ No run directories found in {runs_folder}")

            run_name = run_dirs[0].name
            rprint(
                f"ℹ️  [bold]`run_name` not provided[/bold], using latest run: [green]{run_name}[/green]"
            )

        try:
            SolverLayer.visualize_2D(
                workspace_path,
                run_name,
                output_folder,
                frame_format=frame_format,
                include_axis=include_axis,
                transparent=transparent,
                units=units,
            )
            rprint(f"✅ Finished visualizing")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
            raise typer.Exit(code=1)

    return solver_visualize
