import os
import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_solver_run_layer(app: typer.Typer):
    @app.command(name="run-layer")
    def solver_run_layer(
        segments_foldername: Annotated[
            str, typer.Argument(help="Name of the folder that contains the segments.")
        ],
        layer_index: Annotated[
            int, typer.Argument(help="Use segments within specified layer index")
        ],
        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build Parameters filename")
        ] = "default.json",
        material_filename: Annotated[
            str, typer.Option("--material", help="Material filename")
        ] = "default.json",
        mesh_parameters_filename: Annotated[
            str, typer.Option("--mesh-config", help="Mesh config filename")
        ] = "default.json",
        model_name: Annotated[
            str,
            typer.Option(
                "--model-name",
                help="One of either 'eagar-tsai', 'rosenthal', 'surrogate'",
            ),
        ] = "eagar-tsai",
        run_name: Annotated[
            str | None,
            typer.Option("--run-name", help="Run name used for saving to mesh folder"),
        ] = None,
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """Run solver for a specified layer of segments."""
        import json

        from am.config import BuildParameters, Material, MeshParameters, Segment
        from am.solver.layer import SolverLayer

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            solver_layer = SolverLayer()
            # Segments
            segments_path = workspace_path / "segments" / segments_foldername / "layers"

            # Uses number of files in segments path as total layers for zfill.
            total_layers = len(os.listdir(segments_path))
            z_fill = len(f"{total_layers}")
            layer_index_string = f"{layer_index}".zfill(z_fill)
            segments_file_path = segments_path / f"{layer_index_string}.json"

            # TODO: Settle on a better way to handle loading of lists of a particular schema.
            with open(segments_file_path, "r") as f:
                segments_data = json.load(f)
            segments = [Segment(**seg_data) for seg_data in segments_data]
            # segments = Segment.load(segments_file_path)

            # Configs
            # TODO: Add in checks for subfolders and throw specific errors with
            # information on how to create subfolder.

            build_parameters = BuildParameters.load(
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )
            material = Material.load(
                workspace_path / "configs" / "materials" / material_filename
            )
            mesh_parameters = MeshParameters.load(
                workspace_path
                / "configs"
                / "mesh_parameters"
                / mesh_parameters_filename
            )

            solver_layer.run(
                segments,
                build_parameters,
                material,
                mesh_parameters,
                workspace_path,
                model_name,
                run_name,
            )
            rprint(f"✅ Solver Finished")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to run solver for layer: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="run-layer")(solver_run_layer)
    return solver_run_layer
