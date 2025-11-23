import typer

from pathlib import Path
from rich import print as rprint

from am.process_map.plot import PlotType

from am.cli.options import NumProc


def register_process_map_plot(app: typer.Typer):
    @app.command(name="plot")
    def process_map_plot(
        process_map_folder_name: str,
        plot_type: PlotType,
        workspace_name: str,
        # workspaces_path: Path | None = None,
    ) -> None:
        """
        Plot the points generated for a process map.
        """

        from am.process_map.plot import plot_process_map
        from am.process_map.models import ProcessMapPoints
        from am.process_map.utils import process_map_points_to_plot_data

        from wa.cli.utils import get_workspace_path

        # try:
        workspace_path = get_workspace_path(workspace_name)

        process_map_path = workspace_path / "process_maps" / process_map_folder_name

        process_map_points_path = process_map_path / "points.json"

        process_map_points = ProcessMapPoints.load(process_map_points_path)

        plot_data = process_map_points_to_plot_data(process_map_points)

        plot_process_map(process_map_path, plot_data, plot_type)

        # except FileExistsError as e:
        #     rprint(f"⚠️  [yellow]Process Map: `{process_map_folder_name}` already exists.[/yellow]")
        #     rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
        #     _ = typer.Exit()
        # except:
        #     rprint("⚠️  [yellow]Unable to run process map[/yellow]")
        #     _ = typer.Exit()
