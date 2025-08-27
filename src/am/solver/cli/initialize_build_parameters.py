import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import VerboseOption


# TODO: Add in more customizability for generating build configs.
def register_solver_initialize_build_parameters(app: typer.Typer):
    @app.command(name="initialize_build_parameters")
    def solver_initialize_build_parameters(
        build_name: str | None = "default",
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.schema import BuildParameters

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
        build_parameters = BuildParameters.create_default()
        default_save_path = cwd / "solver" / "config" / "build" / "default.json"
        save_path = build_parameters.save(default_save_path)
        rprint(f"✅ Initialized solver build at {save_path}")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize solver: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="init_build_parameters")(solver_initialize_build_parameters)
    return solver_initialize_build_parameters
