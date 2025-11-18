import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption


def register_config_mesh_parameters(app: typer.Typer):
    from am.config.mesh_parameters import DEFAULT

    @app.command(name="mesh-parameters")
    def config_mesh_parameters(
        name: str | None = "default",
        x_step: str | None = typer.Option(
            DEFAULT["x_step"], help='Valid formats: 5, "5", "5 um", "(5, \'um\')"'
        ),
        y_step: str | None = typer.Option(
            DEFAULT["y_step"], help='Valid formats: 5, "5", "5 um", "(5, \'um\')"'
        ),
        z_step: str | None = typer.Option(
            DEFAULT["z_step"], help='Valid formats: 5, "5", "5 um", "(5, \'um\')"'
        ),
        x_min: str | None = typer.Option(
            DEFAULT["x_min"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        x_max: str | None = typer.Option(
            DEFAULT["x_max"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        y_min: str | None = typer.Option(
            DEFAULT["y_min"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        y_max: str | None = typer.Option(
            DEFAULT["y_max"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        z_min: str | None = typer.Option(
            DEFAULT["z_min"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        z_max: str | None = typer.Option(
            DEFAULT["z_max"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        x_initial: str | None = typer.Option(
            DEFAULT["x_initial"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        y_initial: str | None = typer.Option(
            DEFAULT["y_initial"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        z_initial: str | None = typer.Option(
            DEFAULT["z_initial"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        x_start_pad: str | None = typer.Option(
            DEFAULT["x_start_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        y_start_pad: str | None = typer.Option(
            DEFAULT["y_start_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        z_start_pad: str | None = typer.Option(
            DEFAULT["z_start_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        x_end_pad: str | None = typer.Option(
            DEFAULT["x_end_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        y_end_pad: str | None = typer.Option(
            DEFAULT["y_end_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        z_end_pad: str | None = typer.Option(
            DEFAULT["z_end_pad"], help='Valid formats: 5, "5", "5 mm", "(5, \'mm\')"'
        ),
        boundary_condition: str | None = typer.Option(
            "temperature", help="Boundary condition type: 'flux' or 'temperature'"
        ),
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for mesh parameters."""
        from am.config import MeshParameters
        from pintdantic import parse_cli_input
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            mesh_parameters = MeshParameters(
                x_step=parse_cli_input(x_step),
                y_step=parse_cli_input(y_step),
                z_step=parse_cli_input(z_step),
                x_min=parse_cli_input(x_min),
                x_max=parse_cli_input(x_max),
                y_min=parse_cli_input(y_min),
                y_max=parse_cli_input(y_max),
                z_min=parse_cli_input(z_min),
                z_max=parse_cli_input(z_max),
                x_initial=parse_cli_input(x_initial),
                y_initial=parse_cli_input(y_initial),
                z_initial=parse_cli_input(z_initial),
                x_start_pad=parse_cli_input(x_start_pad),
                y_start_pad=parse_cli_input(y_start_pad),
                z_start_pad=parse_cli_input(z_start_pad),
                x_end_pad=parse_cli_input(x_end_pad),
                y_end_pad=parse_cli_input(y_end_pad),
                z_end_pad=parse_cli_input(z_end_pad),
                boundary_condition=boundary_condition,
            )
            save_path = workspace_path / "config" / "mesh_parameters" / f"{name}.json"
            mesh_parameters.save(save_path)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create mesh parameters file: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="mesh-parameters")(config_mesh_parameters)
    return config_mesh_parameters
