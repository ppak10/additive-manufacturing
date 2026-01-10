import typer

from typing_extensions import Annotated

ParameterShorthandOption = typer.Option(
    help="Parameter Shorthand: <name> [<min> <max> <step>] [<units>] (i.e. --p1 beam_power 100 300 50 watts)"
)
ParameterNameOption = typer.Option(
    help="Parameter Name: 'beam_power', 'scan_velocity', 'layer_height', 'hatch_spacing'"
)
ParameterRangeOption = typer.Option(
    help="Parameter Range: <min> <max> <step> (i.e. 100 1000 100)"
)
ParameterUnitsOption = typer.Option(
    help="Parameter Units: 'W', 'm/s', 'mm/s', 'microns', etc."
)


def register_simulator_process_map(app: typer.Typer):
    from pathlib import Path

    from am.cli.options import NumProc, VerboseOption
    from wa.cli.options import WorkspaceOption

    @app.command(name="process-map", rich_help_panel="Simulator Commands")
    def simulator_process_map(
        material_filename: Annotated[
            str, typer.Option("--material", help="Material configuration filename")
        ] = "default.json",
        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build parameters filename")
        ] = "default.json",
        # Parameter 1
        p1: Annotated[list[str] | None, ParameterShorthandOption] = None,
        p1_name: Annotated[str | None, ParameterNameOption] = None,
        p1_range: Annotated[list[int] | None, ParameterRangeOption] = None,
        p1_units: Annotated[str | None, ParameterUnitsOption] = None,
        # Parameter 2
        p2: Annotated[list[str] | None, ParameterShorthandOption] = None,
        p2_name: Annotated[str | None, ParameterNameOption] = None,
        p2_range: Annotated[list[int] | None, ParameterRangeOption] = None,
        p2_units: Annotated[str | None, ParameterUnitsOption] = None,
        # Parameter 3
        p3: Annotated[list[str] | None, ParameterShorthandOption] = None,
        p3_name: Annotated[str | None, ParameterNameOption] = None,
        p3_range: Annotated[list[int] | None, ParameterRangeOption] = None,
        p3_units: Annotated[str | None, ParameterUnitsOption] = None,
        workspace_name: WorkspaceOption = None,
        num_proc: NumProc = 1,
        visualize: bool = False,
        verbose: VerboseOption = False,
    ) -> None:
        """
        Generate a process map by varying build parameters.

        Examples:
            # Shorthand notation
            am simulator process-map material.json --p1 beam_power 100 300 50 watts

            # Verbose notation
            am simulator process-map material.json --p1-name beam_power --p1-range 100 300 50 --p1-units watts

            # Mixed (units inferred from parameter name)
            am simulator process-map material.json --p1 beam_power 100 300 50

            # Multiple parameters
            am simulator process-map material.json --p1 beam_power 100 300 50 --p2 scan_velocity 0.5 1.5 0.25

            # Just parameter name (must provide range separately or use defaults)
            am simulator process-map material.json --p1-name beam_power
        """
        from rich import print as rprint

        from am.config import BuildParameters, Material
        from am.simulator.tool.process_map.models import ProcessMap
        from am.simulator.tool.process_map.utils.parameter_ranges import (
            inputs_to_parameter_ranges,
        )
        from wa.cli.utils import get_workspace

        try:
            workspace = get_workspace(workspace_name)

            # Parse and validate parameters
            parameter_ranges = inputs_to_parameter_ranges(
                (p1, p1_name, p1_range, p1_units),
                (p2, p2_name, p2_range, p2_units),
                (p3, p3_name, p3_range, p3_units),
            )

            # Load material and build parameters
            material = Material.load(
                workspace.path / "configs" / "materials" / material_filename
            )

            build_parameters = BuildParameters.load(
                workspace.path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            # Create output folder
            process_map_path = Path("simulations/process_map") / material.name
            workspace_folder = workspace.create_folder(
                name_or_path=process_map_path,
                append_timestamp=True,
            )

            if verbose:
                rprint(
                    f"[cyan]Creating process map with {len(parameter_ranges)} parameter(s)[/cyan]"
                )
                rprint(f"[cyan]Output: {workspace_folder.path}[/cyan]")

            # Create ProcessMap
            process_map = ProcessMap(
                build_parameters=build_parameters,
                material=material,
                parameter_ranges=parameter_ranges,
                out_path=workspace_folder.path,
            )

            process_map.run(num_proc=num_proc)

            if visualize:
                process_map.plot()

            process_map.save()

            # TODO: Generate process map
            rprint(f"✅ [green]Process map created successfully[/green]")
            rprint(f"   Output: {workspace_folder.path}")

        except typer.Exit:
            raise
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to generate process map: {e}[/yellow]")
            if verbose:
                import traceback

                traceback.print_exc()
            raise typer.Exit(code=1)

    return simulator_process_map
