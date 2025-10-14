import os
import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_segmenter_visualize_layer(app: typer.Typer):
    @app.command(name="visualize-layer")
    def segmenter_visualize_layer(
        segments_name: Annotated[str, typer.Argument(help="Segments name")],
        layer_number: Annotated[
            int, typer.Argument(help="Layer number of segment to visualize")
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
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from am.segmenter.visualize import SegmenterVisualize

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            # Segments
            segments_path = workspace_path / "segments" / segments_name
            # Uses number of files in segments path as total layers for zfill.
            segment_layers_path = segments_path / "layers"
            total_layers = len(os.listdir(segment_layers_path))
            z_fill = len(f"{total_layers}")
            layer_number_string = f"{layer_number}".zfill(z_fill)
            segment_layer_file_path = (
                segment_layers_path / f"{layer_number_string}.json"
            )

            segmenter = SegmenterVisualize()
            _ = segmenter.load_segments(segment_layer_file_path)

            print("loaded segments")

            segmenter.visualize(
                segments_path=segments_path,
                visualization_name=f"layer_{layer_number_string}",
                color=color,
                frame_format=frame_format,
                include_axis=include_axis,
                linewidth=linewidth,
                transparent=transparent,
                units=units,
                verbose=verbose,
            )

            rprint(f"✅ Successfully generated segment visualizations")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to complete visualizations: {e}[/yellow]")
            raise typer.Exit(code=1)

    return segmenter_visualize_layer
