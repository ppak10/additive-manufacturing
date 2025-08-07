from mcp.server.fastmcp import FastMCP, Context

from pathlib import Path
from typing import Union

def register_segmenter(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.segmenter.config import SegmenterConfig
    
    @app.tool(
        title="Segmenter Initialization",
        description="Initializes segmenter within workspace folder.",
        structured_output=True,
    )
    def segmenter_initialize(
        workspace_name: str,
        include_examples: bool = True,
    ) -> Union[ToolSuccess[SegmenterConfig], ToolError]:
        """Create a folder to perform and store segmenter operations"""
        from am.segmenter import Segmenter
        from am.workspace import WorkspaceConfig

        
        try:
            project_root = WorkspaceConfig.get_project_root_from_package()
            workspace_dir = project_root / "out" / workspace_name
            config_file = workspace_dir / "config.json"

            if not config_file.exists():
                return tool_error(
                    "Workspace `config.json` does not exist",
                    "WORKSPACE_NOT_FOUND", 
                    workspace_name=workspace_name,
                )

            segmenter = Segmenter()
            segmenter_config = segmenter.initialize(
                segmenter_path=workspace_dir / "segmenter", include_examples=include_examples
            )
            return tool_success(segmenter_config)
            
        except PermissionError as e:
            return tool_error(
                "Permission denied when initializing segmenter",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )
            
        except Exception as e:
            return tool_error(
                "Failed to create segmenter",
                "SEGMENTER_CREATE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )

    @app.tool(
        title="Segmenter Parse", 
        description="Uses segmenter to parse a specified file",
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
        Parses a specified file within the `segmenter/parts` folder.
        Args:
            ctx: Context for long running task
            workspace_name: Folder name of existing workspace
            filename: Filename desired file to parse with extension (i.e. overhang.gcode)
            distance_xy_max: Maximum segment length when parsing (defaults to 1.0 mm).
            units: Defined units of gcode file.
        """

        from am.segmenter import SegmenterConfig, SegmenterParse
        from am.workspace import WorkspaceConfig
        
        try:
            project_root = WorkspaceConfig.get_project_root_from_package()
            workspace_dir = project_root / "out" / workspace_name
            config_file = workspace_dir / "config.json"

            if not config_file.exists():
                return tool_error(
                    "Workspace `config.json` does not exist",
                    "WORKSPACE_NOT_FOUND", 
                    workspace_name=workspace_name,
                )

            segmenter_dir = workspace_dir / "segmenter"

            segmenter_config = SegmenterConfig.load(segmenter_dir / "config.json")
            segmenter_parse = SegmenterParse(segmenter_config)

            # Assumes file is in `workspace/segmenter/parts/`
            filepath = segmenter_dir / "parts" / filename

            await ctx.info(f"Beginning parse of {filename}")
            _ = await segmenter_parse.gcode_to_commands(filepath, units, context=ctx, verbose=verbose)
            _ = await segmenter_parse.commands_to_segments(
                distance_xy_max=distance_xy_max, units=units, context=ctx, verbose=verbose
            )

            filename_no_ext = filename.split(".")[0]
            segments_path = segmenter_dir / "segments" / f"{filename_no_ext}.json"
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
                exception_message=str(e)
            )

    # TODO: Move parts under workspace/parts and decouple from segmenter.
    @app.resource("workspace://{workspace}/parts")
    def parts_list(workspace: str) -> list[str] | None:
        """
        Lists available parts within workspace
        """
        from am.segmenter import Segmenter
        return Segmenter.list_parts(workspace)

