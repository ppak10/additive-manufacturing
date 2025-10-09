import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from ow.cli.options import WorkspaceOption

# TODO: Deprecate, initialization is not needed
def register_solver_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def solver_initialize(
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """Initializes solver with defaults inside workspace folder."""
        from am.solver.layer import SolverLayer
        from ow.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            solver = SolverLayer()
            solver.create_solver_config(solver_path=workspace_path / "solver")
            solver.create_default_configs()
            rprint(f"✅ Solver initialized")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init")(solver_initialize)
    return solver_initialize
