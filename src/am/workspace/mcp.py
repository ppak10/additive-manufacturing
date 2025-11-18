from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_workspace_create(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from wa.models import Workspace

    @app.tool(
        title="Create Additive Manufacturing Workspace",
        description="Creates workspace with `config` and `parts` folders and files for use with additive manufacturing tools. Use workspace.workspace_management tool for general workspace management.",
        structured_output=True,
    )
    async def workspace_create(
        workspace_name: str,
        workspaces_path: Path | None = None,
        force: bool = False,
        include_examples: bool = False,
    ) -> Union[ToolSuccess[Workspace], ToolError]:
        """
        Initialize additive manufacturing workspace folder with relevant subfolders.

        Args:
            workspace_name: Name of folder to initialize.
            workspaces_path: Path of folder containing workspaces.
            force: Overwrite existing workspace.
            include_examples: Copies examples to workspace folder.
        """
        from am.workspace.create import create_additive_manufacturing_workspace

        try:
            workspace = create_additive_manufacturing_workspace(
                workspace_name=workspace_name,
                workspaces_path=workspaces_path,
                force=force,
                include_examples=include_examples,
            )

            return tool_success(workspace)

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating workspace folder",
                "PERMISSION_DENIED",
                workspace_name=workspace.name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create workspace folder",
                "WORKSPACE_CREATE_FAILED",
                workspace_name=workspace.name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = workspace_create
