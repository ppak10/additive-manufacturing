import typer

from pathlib import Path
from rich import print as rprint

from am.solver import Solver

def register_solver_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def solver_initialize() -> None:
        """Create folder for solver data inside workspace folder."""

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
            raise typer.Exit(code=1)

        # try:
        solver = Solver()
        solver.create_solver(solver_path = cwd / "solver")
        rprint(f"✅ Solver initialized")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="init")(solver_initialize)
    return solver_initialize

