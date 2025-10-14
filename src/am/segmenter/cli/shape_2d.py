import typer

from rich import print as rprint

from am.cli.options import VerboseOption
from wa.cli.options import WorkspaceOption

from typing_extensions import Annotated


def register_segmenter_shape_2d(app: typer.Typer):
    from am.segmenter.shape_2d import Shape, SegmenterShape2D

    @app.command(name="shape-2d")
    def segmenter_shape_2d(
        shape: Shape = Shape.line,
        size: Annotated[float, typer.Option("--size")] = 10.0,
        distance_xy_max: Annotated[float, typer.Option("--distance-xy-max")] = 1.0,
        units: Annotated[str, typer.Option("--units")] = "mm",
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """Create folder for solver data inside workspace folder."""
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        segments_name = f"shape_2d_{shape.value}_{size}_{units}"

        try:
            # Segmenter Shape 2D
            segmenter_shape_2d = SegmenterShape2D()
            segmenter_shape_2d.generate(shape, size, distance_xy_max, units)
            segments_path = workspace_path / "segments" / segments_name
            output_path = segmenter_shape_2d.save_segments(
                segments_path, verbose=verbose
            )
            rprint(f"✅ Created 2d shape `{shape}` saved at `{output_path}`")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to create 2d shape `{shape}`: {e}[/yellow]")
            raise typer.Exit(code=1)

    return segmenter_shape_2d
