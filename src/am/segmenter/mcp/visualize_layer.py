import os

from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_segmenter_visualize_layer(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Segmenter Visualize Layer",
        description="Uses segmenter to visualize a layer of parsed segments under @am:workspace://{workspace}/segments (layer_number starts from 1)",
        structured_output=True,
    )
    async def segmenter_visualize_layer(
        segments: str,
        workspace_name: str,
        layer_number: int,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Visualizes a specified layer within the `{wokspace}/segments/layers` folder.
        Args:
            segments: Folder name for the segments to visualize.
            workspace: Folder name of existing workspace.
            layer_number: Layer number (starts from 1) of part to visualize.
        """

        from am.segmenter.visualize import SegmenterVisualize
        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace_name)

            # Segments
            segments_path = workspace_path / "segments" / segments

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

            animation_out_path = segmenter.visualize(
                segments_path=segments_path,
                visualization_name=f"layer_{layer_number_string}",
            )
            return tool_success(animation_out_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when visualizing segments",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to visualize segments",
                "SEGMENTER_VISUALIZE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = segmenter_visualize_layer
