import importlib.metadata

from rich import print as rprint
import typer


def register_version(app: typer.Typer):
    @app.command()
    def version() -> None:
        """Show the additive-manufacturing version."""
        try:
            version = importlib.metadata.version("additive-manufacturing")
            rprint(f"✅ additive-manufacturing version {version}")
        except importlib.metadata.PackageNotFoundError:
            rprint(
                "⚠️  [yellow]additive-manufacturing version unknown (package not installed)[/yellow]"
            )
            raise typer.Exit()

    return version
