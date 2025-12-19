import os
import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_simulator_residual_heat(app: typer.Typer):
    @app.command(name="residual-heat")
    def simulator_residual_heat(
        toolpath_foldername: Annotated[
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
        solver: Annotated[
            str,
            typer.Option(
                "--solver",
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

        from am.config import BuildParameters, Material, MeshParameters
        from am.simulator.models import SolverLayer
        from am.simulator.residual_heat.run_layer import run_layer

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            # Load toolpath solver segments
            toolpath_solver_data_path = workspace_path / "toolpaths" / toolpath_foldername / "solver" / "data"

            # TODO: Create a toolpath.json file in the folder via workspace for
            # this data.
            # Uses number of files in segments path as total layers for zfill.
            total_layers = len(os.listdir(toolpath_solver_data_path))
            z_fill = len(f"{total_layers}")
            layer_index_string = f"{layer_index}".zfill(z_fill)
            solver_layer_file_path = toolpath_solver_data_path / f"{layer_index_string}.json"
            solver_layer = SolverLayer.load(solver_layer_file_path)

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
                solver,
                run_name,
            )
            rprint(f"✅ Solver Finished")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to run solver for layer: {e}[/yellow]")
            raise typer.Exit(code=1)

    return simulator_residual_heat
