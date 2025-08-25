import typer

from rich import print as rprint

from am.cli.options import VerboseOption, WorkspaceOption

from typing_extensions import Annotated

def register_solver_measure_melt_pool_dimensions(app: typer.Typer):
    @app.command(name="measure_melt_pool_dimensions")
    def solver_measure_melt_pool_dimensions(
        build_config_filename: Annotated[
            str, typer.Option("--build_config", help="Build config filename")
        ] = "default.json",
        material_config_filename: Annotated[
            str, typer.Option("--material_config", help="Material config filename")
        ] = "default.json",
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
        from am.solver.types import BuildConfig, MaterialConfig

        workspace_path = get_workspace_path(workspace)

        try:
            solver = Solver()

            # Configs
            solver_configs_path = workspace_path / "solver" / "config"
            build_config = BuildConfig.load(
                solver_configs_path / "build" / build_config_filename
            )
            material_config = MaterialConfig.load(
                solver_configs_path / "material" / material_config_filename
            )

            solver.measure_melt_pool_dimensions(build_config, material_config, workspace_path, run_name)
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
            raise typer.Exit(code=1)

    return solver_measure_melt_pool_dimensions

