import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


# TODO: Split up this functionality
def register_process_map_generate_melt_pool_measurements(app: typer.Typer):

    @app.command(name="generate")
    def generate_process_map(
        name: str | None = None,
        build_parameters_filename: Annotated[
            str, typer.Option("--build_parameters", help="Build config filename")
        ] = "build_parameters.json",
        material_filename: Annotated[
            str, typer.Option("--material", help="Material config filename")
        ] = "material.json",
        workspace: WorkspaceOption = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create file for build parameters."""
        from am.config import BuildParameters, Material
        from am.process_map.generate import generate_melt_pool_measurements
        from am.process_map.schema import ProcessMap

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        process_maps_folder = workspace_path / "process_maps"

        if name is None:
            # Get list of subdirectories sorted by modification time (newest first)
            process_map_folder = sorted(
                [d for d in process_maps_folder.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )

            if not process_map_folder:
                raise FileNotFoundError(
                    f"❌ No run directories found in {process_maps_folder}"
                )

            name = process_map_folder[0].name
            rprint(
                f"ℹ️  [bold]`name` not provided[/bold], using most recently initialized process_map: [green]{name}[/green]"
            )

        # try:
        # Build Parameters
        build_parameters_path = process_maps_folder / name / build_parameters_filename

        build_parameters = BuildParameters.load(build_parameters_path)

        material_path = process_maps_folder / name / material_filename

        material = Material.load(material_path)

        process_map_config_path = process_maps_folder / name / "config.json"

        process_map = ProcessMap.load(process_map_config_path)

        generate_melt_pool_measurements(
            workspace_path=workspace_path,
            build_parameters=build_parameters,
            material=material,
            process_map=process_map,
            name=name,
        )

        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to create build parameters file: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="generate")(generate_process_map)
    return generate_process_map
