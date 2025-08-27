import typer

from rich import print as rprint

from am.cli.options import VerboseOption, WorkspaceOption


# TODO: Add in more customizability for generating build configs.
def register_schema_build_parameters(app: typer.Typer):
    from am.schema import QuantityInput
    from am.schema.build_parameters import DEFAULT

    @app.command(name="build-parameters")
    def schema_build_parameters(
        name: str | None = "default",
        beam_diameter: QuantityInput = DEFAULT["beam_diameter"],
        beam_power: QuantityInput = DEFAULT["beam_power"],
        scan_velocity: QuantityInput = DEFAULT["scan_velocity"],
        temperature_preheat: QuantityInput = DEFAULT["temperature_preheat"],
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for build parameters."""
        from am.cli.utils import get_workspace_path
        from am.schema import BuildParameters

        workspace_path = get_workspace_path(workspace)

        try:
            build_parameters = BuildParameters(
                beam_diameter=beam_diameter,
                beam_power=beam_power,
                scan_velocity=scan_velocity,
                temperature_preheat=temperature_preheat,
            )
            save_path = workspace_path / "build_parameters" / f"{name}.json"
            build_parameters.save(save_path)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create build parameters file: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="build-parameters")(schema_build_parameters)
    return schema_build_parameters
