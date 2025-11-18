import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption


# TODO: Add in more customizability for generating build configs.
def register_config_build_parameters(app: typer.Typer):
    from am.config.build_parameters import DEFAULT

    @app.command(name="build-parameters")
    def config_build_parameters(
        name: str | None = "default",
        beam_diameter: str | None = typer.Option(
            DEFAULT["beam_diameter"], help='Valid formats: 5, "5", "5 m", "(5, \'m\')"'
        ),
        beam_power: str | None = typer.Option(
            DEFAULT["beam_power"], help='Valid formats: 5, "5", "5 W", "(5, \'W\')"'
        ),
        hatch_spacing: str | None = typer.Option(
            DEFAULT["hatch_spacing"],
            help='Valid formats: 5, "5", "5 microns", "(5, \'microns\')"',
        ),
        layer_height: str | None = typer.Option(
            DEFAULT["layer_height"],
            help='Valid formats: 5, "5", "5 microns", "(5, \'microns\')"',
        ),
        scan_velocity: str | None = typer.Option(
            DEFAULT["scan_velocity"],
            help='Valid formats: 5, "5", "5 m/s", "(5, \'m/s\')"',
        ),
        temperature_preheat: str | None = typer.Option(
            DEFAULT["temperature_preheat"],
            help='Valid formats: 5, "5", "5 K", "(5, \'K\')"',
        ),
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for build parameters."""
        from pintdantic import parse_cli_input
        from wa.cli.utils import get_workspace_path

        from am.config import BuildParameters

        workspace_path = get_workspace_path(workspace)

        try:
            build_parameters = BuildParameters(
                beam_diameter=parse_cli_input(beam_diameter),
                beam_power=parse_cli_input(beam_power),
                hatch_spacing=parse_cli_input(hatch_spacing),
                layer_height=parse_cli_input(layer_height),
                scan_velocity=parse_cli_input(scan_velocity),
                temperature_preheat=parse_cli_input(temperature_preheat),
            )
            save_path = workspace_path / "config" / "build_parameters" / f"{name}.json"
            build_parameters.save(save_path)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create build parameters file: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="build-parameters")(config_build_parameters)
    return config_build_parameters
