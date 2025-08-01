import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import VerboseOption


# TODO: Add in more customizability for generating material configs.
def register_solver_initialize_material_config(app: typer.Typer):
    @app.command(name="initialize_material_config")
    def solver_initialize_material_config(
        material_name: str | None = "default",
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.solver import SolverConfig
        from am.solver.types import MaterialConfig

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint(
                "❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]"
            )
            raise typer.Exit(code=1)

        solver_config_file = cwd / "solver" / "config.json"

        if not solver_config_file.exists():
            rprint(
                "❌ [red]Solver material config not initialized. `solver/config.json` not found.[/red]"
            )
        try:
            solver_config = SolverConfig.load(solver_config_file)
            material_config = MaterialConfig.create_default(solver_config.ureg)
            default_save_path = cwd / "solver" / "config" / "material" / "default.json"
            save_path = material_config.save(default_save_path)
            rprint(f"✅ Initialized solver material at {save_path}")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init_material_config")(solver_initialize_material_config)
    return solver_initialize_material_config
