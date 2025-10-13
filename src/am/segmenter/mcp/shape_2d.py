from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_segmenter_shape_2d(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.segmenter.shape_2d import Shape, SegmenterShape2D

    @app.tool(
        title="Segmenter Shape 2D",
        description="Allows for generation of segments to a given set of shapes, such as line",
        structured_output=True,
    )
    async def segmenter_shape_2d(
        workspace_name: str,
        shape: Shape = Shape.line,
        size: float = 10.0,
        distance_xy_max: float = 1.0,
        units: str = "mm",
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Creates a single layer of segments for a given primitive shape.
        Args:
            workspace_name: Folder name of existing workspace.
            shape: Right now only `line` is implemented.
            size: Overall length or diameter or the shape.
            distance_xy_max: Maximum distance of segment.
            units: Distance units used for size and distance_xy_max.
        """

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace_name)

        segments_name = f"shape_2d_{shape.value}_{size}_{units}"

        try:
            # Segmenter Shape 2D
            segmenter_shape_2d = SegmenterShape2D()
            segmenter_shape_2d.generate(shape, size, distance_xy_max, units)
            segments_path = workspace_path / "segments" / segments_name
            output_path = segmenter_shape_2d.save_segments(segments_path)
            return tool_success(output_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to generate 2d shape segments",
                "SEGMENTER_SHAPE_2D_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = segmenter_shape_2d
