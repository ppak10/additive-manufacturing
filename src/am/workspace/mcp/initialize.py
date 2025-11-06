from mcp.server.fastmcp import FastMCP, Context

from pathlib import Path
from typing import cast, Union


def register_workspace_initialize(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Initialize Additive Manufacturing Workspace",
        description="Uses workspace-agent package to create a workspace for additive manufacturing with necessary subfolders.",
        structured_output=True,
    )
    async def workspace_initialize(
        name: str,
        out_path: Path | None = None,
        force: bool = False,
        include_examples: bool = False,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Initialize additive manufacturing workspace folder with relevant subfolders.

        Args:
            name: Name of folder to initialize.
            out_path: Path of folder containing workspaces.
            force: Overwrite existing workspace.
            include_examples: Copies examples to workspace folder.
        """
        from wa.workspace.tools.create import create_workspace
        from am.workspace import initialize_configs, initialize_parts

        try:
            workspace = create_workspace(name, out_path, force)
            workspace_path = cast(Path, workspace.workspace_path)

            initialize_configs(workspace_path)
            initialize_parts(workspace_path, include_examples)

            return tool_success(workspace_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when initializing workspace folder",
                "PERMISSION_DENIED",
                workspace_name=name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to initialize workspace folder",
                "WORKSPACE_INITIALIZE_FAILED",
                workspace_name=name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = workspace_initialize
