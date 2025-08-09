import os
import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import VerboseOption

from typing_extensions import Annotated


def register_solver_visualize(app: typer.Typer):
    @app.command(name="visualize")
    def solver_run_layer(
        run_name: Annotated[
            str | None,
            typer.Option("--run_name", help="Run name used for saving to mesh folder"),
        ] = None,
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
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.solver import Solver

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint(
                "❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]"
            )
            raise typer.Exit(code=1)

        runs_folder = cwd / "solver" / "runs"
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
        run_folder = runs_folder / run_name

        # try:
        Solver.visualize_2D(
            run_folder,
            frame_format=frame_format,
            include_axis=include_axis,
            transparent=transparent,
            units=units,
        )
        rprint(f"✅ Finished visualizing")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="visualize")(solver_run_layer)
    return solver_run_layer
