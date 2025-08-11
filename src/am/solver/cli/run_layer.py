import os
import typer

from rich import print as rprint

from am.cli.options import VerboseOption, WorkspaceOption

from typing_extensions import Annotated


def register_solver_run_layer(app: typer.Typer):
    @app.command(name="run_layer")
    def solver_run_layer(
        segments_filename: Annotated[str, typer.Argument(help="Segments filename")],
        layer_index: Annotated[
            int, typer.Argument(help="Use segments within specified layer index")
        ],
        build_config_filename: Annotated[
            str, typer.Option("--build_config", help="Build config filename")
        ] = "default.json",
        material_config_filename: Annotated[
            str, typer.Option("--material_config", help="Material config filename")
        ] = "default.json",
        mesh_config_filename: Annotated[
            str, typer.Option("--mesh_config", help="Mesh config filename")
        ] = "default.json",
        model_name: Annotated[
            str, typer.Option(
                "--model_name",
                help="One of either 'eagar-tsai', 'rosenthal', 'surrogate'"
            )
        ] = "eagar-tsai",
        run_name: Annotated[
            str | None,
            typer.Option("--run_name", help="Run name used for saving to mesh folder"),
        ] = None,
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.cli.utils import get_workspace_path
        from am.solver import Solver
        from am.solver.types import BuildConfig, MaterialConfig, MeshConfig
        from am.segmenter.types import Segment

        workspace_path = get_workspace_path(workspace)

        try:
            solver = Solver()
            # Segments
            segments_path = workspace_path / "segments" / segments_filename / "layers"

            # Uses number of files in segments path as total layers for zfill.
            total_layers = len(os.listdir(segments_path))
            z_fill = len(f"{total_layers}")
            layer_index_string = f"{layer_index}".zfill(z_fill)
            segments_file_path = segments_path / f"{layer_index_string}.json"

            segments = Segment.load(segments_file_path)

            # Configs
            solver_configs_path = workspace_path / "solver" / "config"
            build_config = BuildConfig.load(
                solver_configs_path / "build" / build_config_filename
            )
            material_config = MaterialConfig.load(
                solver_configs_path / "material" / material_config_filename
            )
            mesh_config = MeshConfig.load(
                solver_configs_path / "mesh" / mesh_config_filename
            )

            meshes_path = workspace_path / "meshes"

            solver.run_layer(segments, build_config, material_config, mesh_config, meshes_path, model_name, run_name)
            rprint(f"✅ Solver Finished")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="run_layer")(solver_run_layer)
    return solver_run_layer
