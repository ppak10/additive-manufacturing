import os
import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import VerboseOption

from typing_extensions import Annotated


def register_segmenter_visualize_layer(app: typer.Typer):
    @app.command(name="visualize_layer")
    def segmenter_visualize_layer(
        segments_filename: Annotated[str, typer.Argument(help="Segments filename")],
        layer_index: Annotated[
            int, typer.Argument(help="Use segments within specified layer index")
        ],
        color: Annotated[
            str, typer.Option(help="Color for plotted segments")
        ] = "black",
        frame_format: Annotated[
            str, typer.Option(help="File extension to save frames in")
        ] = "png",
        include_axis: Annotated[
            bool, typer.Option(help="Toggle for including labels, ticks, and spines")
        ] = True,
        linewidth: Annotated[
            float, typer.Option(help="Line width for plotted segments")
        ] = 2.0,
        transparent: Annotated[
            bool, typer.Option(help="Toggle for transparent background")
        ] = False,
        units: Annotated[str, typer.Option(help="Units for plotting segments")] = "mm",
        verbose: VerboseOption = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.segmenter import Segmenter

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        config_file = cwd / "config.json"
        if not config_file.exists():
            rprint(
                "❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]"
            )
            raise typer.Exit(code=1)

        # try:
        # Segments
        segments_path = cwd / "segmenter" / "segments" / segments_filename
        # Uses number of files in segments path as total layers for zfill.
        total_layers = len(os.listdir(segments_path))
        z_fill = len(f"{total_layers}")
        layer_index_string = f"{layer_index}".zfill(z_fill)
        segments_file_path = segments_path / f"{layer_index_string}.json"
        segmenter = Segmenter()
        _ = segmenter.load_segments(segments_file_path)
        segmenter.visualize(
            visualize_name=segments_filename,
            color=color,
            frame_format=frame_format,
            include_axis=include_axis,
            linewidth=linewidth,
            transparent=transparent,
            units=units,
            verbose=verbose,
        )

        rprint(f"✅ Successfully generated segment visualizations")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to complete visualizations: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    _ = app.command(name="visualize_layer")(segmenter_visualize_layer)
    return segmenter_visualize_layer
