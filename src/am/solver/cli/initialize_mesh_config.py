import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import VerboseOption


# TODO: Add in more customizability for generating mesh configs.
def register_solver_initialize_mesh_config(app: typer.Typer):
    @app.command(name="initialize_mesh_config")
    def solver_initialize_mesh_config(
        mesh_name: str | None = "default",
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.solver import SolverConfig
        from am.solver.types import MeshConfig

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
                "❌ [red]Segmenter not initialized. `segmenter/config.json` not found.[/red]"
            )
        # try:
        solver_config = SolverConfig.load(solver_config_file)
        mesh_config = MeshConfig.create_default(solver_config.ureg)
        default_save_path = cwd / "solver" / "config" / "mesh" / "default.json"
        save_path = mesh_config.save(default_save_path)
        rprint(f"✅ Initialized solver mesh at {save_path}")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="init_mesh_config")(solver_initialize_mesh_config)
    return solver_initialize_mesh_config
