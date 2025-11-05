import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption


def register_config_material(app: typer.Typer):
    from am.config.material import DEFAULT

    @app.command(name="material")
    def config_material(
        name: str | None = "default",
        specific_heat_capacity: str | None = typer.Option(
            DEFAULT["specific_heat_capacity"],
            help='Valid formats: 5, "5", "5 J/(kg*K)", "(5, \'J/(kg*K)\')"',
        ),
        absorptivity: str | None = typer.Option(
            DEFAULT["absorptivity"],
            help='Valid formats: 5, "5", "5 dimensionless", "(5, \'dimensionless\')"',
        ),
        thermal_conductivity: str | None = typer.Option(
            DEFAULT["thermal_conductivity"],
            help='Valid formats: 5, "5", "5 W/(m*K)", "(5, \'W/(m*K)\')"',
        ),
        density: str | None = typer.Option(
            DEFAULT["density"],
            help='Valid formats: 5, "5", "5 kg/m**3", "(5, \'kg/m**3\')"',
        ),
        temperature_melt: str | None = typer.Option(
            DEFAULT["temperature_melt"],
            help='Valid formats: 5, "5", "5 K", "(5, \'K\')"',
        ),
        temperature_liquidus: str | None = typer.Option(
            DEFAULT["temperature_liquidus"],
            help='Valid formats: 5, "5", "5 K", "(5, \'K\')"',
        ),
        temperature_solidus: str | None = typer.Option(
            DEFAULT["temperature_solidus"],
            help='Valid formats: 5, "5", "5 K", "(5, \'K\')"',
        ),
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for material."""
        from am.config import Material

        from pintdantic import parse_cli_input
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            material = Material(
                specific_heat_capacity=parse_cli_input(specific_heat_capacity),
                absorptivity=parse_cli_input(absorptivity),
                thermal_conductivity=parse_cli_input(thermal_conductivity),
                density=parse_cli_input(density),
                temperature_melt=parse_cli_input(temperature_melt),
                temperature_liquidus=parse_cli_input(temperature_liquidus),
                temperature_solidus=parse_cli_input(temperature_solidus),
            )
            save_path = workspace_path / "config" / "materials" / f"{name}.json"
            material.save(save_path)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create material file: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="material")(config_material)
    return config_material
