import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_process_map_initialize_power_velocity_range(app: typer.Typer):

    @app.command(name="initialize-power-velocity-range")
    def initialize_process_map_power_velocity_range(
        name: str | None = "default",
        build_parameters_filename: Annotated[
            str, typer.Option("--build_parameters", help="Build config filename")
        ] = "default.json",
        material_filename: Annotated[
            str, typer.Option("--material", help="Material config filename")
        ] = "default.json",
        beam_power_min: Annotated[
            int, typer.Option("--power-min", help="Range Start")
        ] = 0,
        beam_power_max: Annotated[
            int, typer.Option("--power-max", help="Range Stop")
        ] = 1000,
        beam_power_step: Annotated[
            int, typer.Option("--power-step", help="Range Step")
        ] = 100,
        beam_power_units: str = "W",
        scan_velocity_min: Annotated[
            int, typer.Option("--scan-velocity-min", help="Range Start")
        ] = 0,
        scan_velocity_max: Annotated[
            int, typer.Option("--scan-velocity-max", help="Range Stop")
        ] = 1000,
        scan_velocity_step: Annotated[
            int, typer.Option("--scan-velocity-step", help="Range Step")
        ] = 100,
        scan_velocity_units: str = "mm/s",
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for build parameters."""
        from am.config import BuildParameters, Material
        from am.process_map.initialize import initialize_power_velocity_range

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            # Build Parameters
            build_parameters_path = (
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            build_parameters = BuildParameters.load(build_parameters_path)

            material = Material.load(
                workspace_path / "configs" / "materials" / material_filename
            )

            out_path = initialize_power_velocity_range(
                workspace_path=workspace_path,
                build_parameters=build_parameters,
                material=material,
                name=name,
                beam_power_range=[beam_power_min, beam_power_max, beam_power_step],
                beam_power_units=beam_power_units,
                scan_velocity_range=[
                    scan_velocity_min,
                    scan_velocity_max,
                    scan_velocity_step,
                ],
                scan_velocity_units=scan_velocity_units,
            )
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create build parameters file: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init-pv-range")(initialize_process_map_power_velocity_range)
    return initialize_process_map_power_velocity_range
