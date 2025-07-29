import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption

def register_segmenter_initialize(app: typer.Typer):
    @app.command(name="initialize")
    def segmenter_initialize(
        verbose: VerboseOption | None = False,
        include_examples: Annotated[
            bool, typer.Option(
                "--include_examples",
                help="Copy over examples from package"
            )
        ] = True,
    ) -> None:
        """Create folder for segmenter data inside workspace folder."""
        from am.segmenter import Segmenter

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
            raise typer.Exit(code=1)

        try:
            segmenter = Segmenter()
            segmenter.initialize(
                segmenter_path = cwd / "segmenter",
                include_examples = include_examples
            )
            rprint(f"✅ Segmenter initialized")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="init")(segmenter_initialize)
    return segmenter_initialize

