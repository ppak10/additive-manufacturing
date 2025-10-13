# import typer
#
# from rich import print as rprint
#
# from am.cli.options import VerboseOption
# from wa.cli.options import WorkspaceOption
#
# from typing_extensions import Annotated
#
#
# def register_solver_measure_melt_pool_dimensions(app: typer.Typer):
#     @app.command(name="measure-melt-pool-dimensions")
#     def solver_measure_melt_pool_dimensions(
#         build_parameters_filename: Annotated[
#             str, typer.Option("--build_parameters", help="Build parameters filename")
#         ] = "default.json",
#         material_filename: Annotated[
#             str, typer.Option("--material", help="Material filename")
#         ] = "default.json",
#         run_name: Annotated[
#             str | None,
#             typer.Option("--run_name", help="Run name used for saving to mesh folder"),
#         ] = None,
#         workspace: WorkspaceOption = None,
#         verbose: VerboseOption = False,
#     ) -> None:
#         """Create folder for solver data inside workspace folder."""
#         from wa.cli.utils import get_workspace_path
#         from am.schema import BuildParameters, Material
#         from am.solver.layer import SolverLayer
#
#         workspace_path = get_workspace_path(workspace)
#
#         try:
#             solver = SolverLayer()
#
#             # Configs
#             solver_configs_path = workspace_path / "solver" / "config"
#             build_parameters = BuildParameters.load(
#                 solver_configs_path / "build_parameters" / build_parameters_filename
#             )
#             material = Material.load(
#                 solver_configs_path / "materials" / material_filename
#             )
#
#             solver.measure_melt_pool_dimensions(
#                 build_parameters, material, workspace_path, run_name
#             )
#         except Exception as e:
#             rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
#             raise typer.Exit(code=1)
#
#     return solver_measure_melt_pool_dimensions
