import importlib.metadata
import typer

from rich import print as rprint


def register_version(app: typer.Typer):
    @app.command()
    def version() -> None:
        """Show the installed version of `additive-manufacturing` package."""
        try:
            version = importlib.metadata.version("additive-manufacturing")
            rprint(f"✅ additive-manufacturing version {version}")
        except importlib.metadata.PackageNotFoundError:
            rprint(
                "⚠️  [yellow]additive-manufacturing version unknown (package not installed)[/yellow]"
            )
            raise typer.Exit()

    return version
