from mcp.server.fastmcp import FastMCP, Context

from pathlib import Path
from typing import Union


def register_part_initialize(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Part Initialize",
        description="Creates a `parts` subfolder within a workspace",
        structured_output=True,
    )
    async def part_initialize(
        ctx: Context,
        workspace_name: str,
        include_defaults: bool = False,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Initialize parts folder within workspace.

        Args:
            ctx: Context for long running task
            workspace_name: Folder name of existing workspace
            include_defaults: If True, copies default part files from data directory
        """
        from wa.cli.utils import get_workspace_path
        from am.part.initialize import initialize_parts_folder

        try:
            workspace_path = get_workspace_path(workspace_name)

            parts_dir, copied_files = initialize_parts_folder(
                workspace_path, include_defaults
            )

            if copied_files is not None:
                await ctx.info(
                    f"Parts folder initialized at {parts_dir} with {len(copied_files)} default files"
                )
            else:
                await ctx.info(f"Parts folder initialized at {parts_dir}")

            return tool_success(parts_dir)

        except FileNotFoundError as e:
            return tool_error(
                "Data parts directory not found",
                "DATA_PARTS_NOT_FOUND",
                workspace_name=workspace_name,
                exception_message=str(e),
            )

        except PermissionError as e:
            return tool_error(
                "Permission denied when initializing parts folder",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to initialize parts folder",
                "PART_INITIALIZE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = part_initialize
