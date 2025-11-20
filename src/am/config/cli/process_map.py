import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_config_process_map(app: typer.Typer):

    @app.command(name="process-map")
    def config_process_map(
        name: Annotated[
            str, typer.Option(help="Name for the process map config")
        ] = "default",
        # Parameter 1
        p1_parameter: Annotated[
            str | None,
            typer.Option("--p1-parameter", help="Parameter 1 name (e.g., beam_power)"),
        ] = None,
        p1_min: Annotated[
            float | None, typer.Option("--p1-min", help="Parameter 1 minimum value")
        ] = None,
        p1_max: Annotated[
            float | None, typer.Option("--p1-max", help="Parameter 1 maximum value")
        ] = None,
        p1_step: Annotated[
            float | None, typer.Option("--p1-step", help="Parameter 1 step size")
        ] = None,
        p1_unit: Annotated[
            str | None,
            typer.Option(
                "--p1-unit", help="Parameter 1 unit (e.g., watt, meter/second)"
            ),
        ] = None,
        # Parameter 2
        p2_parameter: Annotated[
            str | None,
            typer.Option(
                "--p2-parameter", help="Parameter 2 name (e.g., scan_velocity)"
            ),
        ] = None,
        p2_min: Annotated[
            float | None, typer.Option("--p2-min", help="Parameter 2 minimum value")
        ] = None,
        p2_max: Annotated[
            float | None, typer.Option("--p2-max", help="Parameter 2 maximum value")
        ] = None,
        p2_step: Annotated[
            float | None, typer.Option("--p2-step", help="Parameter 2 step size")
        ] = None,
        p2_unit: Annotated[
            str | None,
            typer.Option(
                "--p2-unit", help="Parameter 2 unit (e.g., watt, meter/second)"
            ),
        ] = None,
        # Parameter 3
        p3_parameter: Annotated[
            str | None,
            typer.Option(
                "--p3-parameter", help="Parameter 3 name (e.g., hatch_spacing)"
            ),
        ] = None,
        p3_min: Annotated[
            float | None, typer.Option("--p3-min", help="Parameter 3 minimum value")
        ] = None,
        p3_max: Annotated[
            float | None, typer.Option("--p3-max", help="Parameter 3 maximum value")
        ] = None,
        p3_step: Annotated[
            float | None, typer.Option("--p3-step", help="Parameter 3 step size")
        ] = None,
        p3_unit: Annotated[
            str | None,
            typer.Option(
                "--p3-unit", help="Parameter 3 unit (e.g., watt, meter/second)"
            ),
        ] = None,
        workspace_name: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """
        Create process map configuration file using parameter ranges.

        Specify 1-3 parameters with their min, max, step, and unit values.
        The process map will generate a Cartesian product of all parameter combinations.

        Example:
            am config process-map --p1-parameter beam_power --p1-min 100 --p1-max 300 --p1-step 100 --p1-unit watt \\
                                  --p2-parameter scan_velocity --p2-min 0.5 --p2-max 1.5 --p2-step 0.5 --p2-unit "meter/second"
        """
        from am.config.process_map import ProcessMap
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        try:
            # Build parameter_ranges list
            parameter_ranges = []

            # Parameter 1
            if p1_parameter:
                if not all(
                    [
                        p1_min is not None,
                        p1_max is not None,
                        p1_step is not None,
                        p1_unit,
                    ]
                ):
                    rprint(
                        f"⚠️  [yellow]For parameter 1, all of --p1-min, --p1-max, --p1-step, and --p1-unit must be provided[/yellow]"
                    )
                    raise typer.Exit(code=1)
                parameter_ranges.append(
                    {
                        p1_parameter: (
                            [p1_min, p1_unit],
                            [p1_max, p1_unit],
                            [p1_step, p1_unit],
                        )
                    }
                )

            # Parameter 2
            if p2_parameter:
                if not all(
                    [
                        p2_min is not None,
                        p2_max is not None,
                        p2_step is not None,
                        p2_unit,
                    ]
                ):
                    rprint(
                        f"⚠️  [yellow]For parameter 2, all of --p2-min, --p2-max, --p2-step, and --p2-unit must be provided[/yellow]"
                    )
                    raise typer.Exit(code=1)
                parameter_ranges.append(
                    {
                        p2_parameter: (
                            [p2_min, p2_unit],
                            [p2_max, p2_unit],
                            [p2_step, p2_unit],
                        )
                    }
                )

            # Parameter 3
            if p3_parameter:
                if not all(
                    [
                        p3_min is not None,
                        p3_max is not None,
                        p3_step is not None,
                        p3_unit,
                    ]
                ):
                    rprint(
                        f"⚠️  [yellow]For parameter 3, all of --p3-min, --p3-max, --p3-step, and --p3-unit must be provided[/yellow]"
                    )
                    raise typer.Exit(code=1)
                parameter_ranges.append(
                    {
                        p3_parameter: (
                            [p3_min, p3_unit],
                            [p3_max, p3_unit],
                            [p3_step, p3_unit],
                        )
                    }
                )

            if not parameter_ranges:
                rprint(
                    f"⚠️  [yellow]At least one parameter must be specified (--p1-parameter, --p2-parameter, or --p3-parameter)[/yellow]"
                )
                raise typer.Exit(code=1)

            # Create ProcessMap with parameter_ranges
            if verbose:
                rprint(
                    f"[cyan]Creating ProcessMap with {len(parameter_ranges)} parameter(s)...[/cyan]"
                )

            process_map = ProcessMap(parameter_ranges=parameter_ranges)

            if verbose:
                rprint(
                    f"[green]Generated {len(process_map.points)} points from parameter ranges[/green]"
                )

            # Save to file
            save_path = workspace_path / "configs" / "process_maps" / f"{name}.json"
            process_map.save(save_path)

            rprint(f"✅ [green]Process map saved to:[/green] {save_path}")
            if verbose:
                rprint(f"   Parameters: {process_map.parameters}")
                rprint(f"   Total points: {len(process_map.points)}")

        except typer.Exit:
            raise
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create process map file: {e}[/yellow]")
            if verbose:
                import traceback

                traceback.print_exc()
            raise typer.Exit(code=1)

    return config_process_map
