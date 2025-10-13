from mcp.server.fastmcp import FastMCP, Context

from pathlib import Path
from typing import Union


def register_segmenter_parse(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Segmenter Parse",
        description="Uses segmenter to parse a specified part file under @am:workspace://{workspace_name}/part",
        structured_output=True,
    )
    async def segmenter_parse(
        ctx: Context,
        workspace_name: str,
        filename: str,
        distance_xy_max: float = 1.0,
        units: str = "mm",
        verbose: bool = False,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Parses a specified file within the `{workspace}/parts` folder.
        Args:
            ctx: Context for long running task
            workspace_name: Folder name of existing workspace
            filename: Filename of `.gcode` part to parse (Parts under @am:workspace://{workspace}/part)
            distance_xy_max: Maximum segment length when parsing (defaults to 1.0 mm).
            units: Defined units of gcode file.
        """

        from am.segmenter import SegmenterParse
        from wa.cli.utils import get_workspace_path

        try:
            # project_root = WorkspaceConfig.get_project_root_from_package()
            # workspace_dir = project_root / "out" / workspace_name
            # config_file = workspace_dir / "config.json"
            #
            # if not config_file.exists():
            #     return tool_error(
            #         "Workspace `config.json` does not exist",
            #         "WORKSPACE_NOT_FOUND",
            #         workspace_name=workspace_name,
            #     )

            workspace_path = get_workspace_path(workspace_name)

            segmenter_parse = SegmenterParse()

            filepath = workspace_path / "parts" / filename

            await ctx.info(f"Beginning parse of {filename}")
            _ = await segmenter_parse.gcode_to_commands(
                filepath, units, context=ctx, verbose=verbose
            )
            _ = await segmenter_parse.commands_to_segments(
                distance_xy_max=distance_xy_max,
                units=units,
                context=ctx,
                verbose=verbose,
            )

            filename_no_ext = filename.split(".")[0]
            segments_path = workspace_path / "segments" / f"{filename_no_ext}.json"
            output_path = segmenter_parse.save_segments(segments_path)

            return tool_success(output_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when parsing file with segmenter",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to parse specified file with segmenter",
                "SEGMENTER_PARSE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = segmenter_parse
