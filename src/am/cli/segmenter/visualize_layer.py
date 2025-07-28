import os
import typer

from pathlib import Path
from rich import print as rprint

from am.segmenter import Segmenter
from am.segmenter.types import Segment
from am.cli.options import VerboseOption

from typing_extensions import Annotated

def register_segmenter_visualize_layer(app: typer.Typer):
    @app.command(name="visualize_layer")
    def segmenter_visualize_layer(
        segments_filename: Annotated[
            str, typer.Argument(
                help="Segments filename"
            )
        ],
        layer_index: Annotated[
            int, typer.Argument(
                help="Use segments within specified layer index"
            )
        ],
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
            raise typer.Exit(code=1)

        try:
            # Segments
            segments_path = cwd / "segmenter" / "segments" / segments_filename
            # Uses number of files in segments path as total layers for zfill.
            total_layers = len(os.listdir(segments_path))
            z_fill = len(f"{total_layers}")
            layer_index_string = f"{layer_index}".zfill(z_fill)
            segments_file_path = segments_path / f"{layer_index_string}.json"
            segmenter = Segmenter()
            _ = segmenter.load_segments(segments_file_path)
            _ = segmenter.visualize(visualize_name = segments_filename)

            rprint(f"✅ Segmenter visualizing layer...")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to complete visualizations: {e}[/yellow]")
            raise typer.Exit(code=1)

    _ = app.command(name="visualize_layer")(segmenter_visualize_layer)
    return segmenter_visualize_layer

