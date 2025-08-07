from mcp.server import FastMCP

from typing import Union

def register_workspace(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.workspace.config import WorkspaceConfig
    
    @app.tool(
        title="Initialize Workspace",
        description="Creates new workspace folder for storing outputs.",
        structured_output=True,
    )
    def workspace_initialize(
        workspace_name: str,
        force: bool = False,
    ) -> Union[ToolSuccess[WorkspaceConfig], ToolError]:
        """Create a folder to store data related to a workspace."""
        from am.workspace import Workspace
        
        try:
            workspace = Workspace(name=workspace_name)
            workspace_config = workspace.create_workspace(force=force)
            return tool_success(workspace_config)
            
        except PermissionError as e:
            return tool_error(
                "Permission denied when creating workspace",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )
            
        except FileExistsError as e:
            return tool_error(
                "Workspace already exists, use `force` to overwrite existing workspace",
                "WORKSPACE_EXISTS", 
                workspace_name=workspace_name,
                suggestion="Use force=True to overwrite",
                exception_message=str(e)
            )
            
        except Exception as e:
            return tool_error(
                "Failed to create workspace",
                "WORKSPACE_CREATE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e)
            )

    @app.resource("workspace://")
    def workspace_list() -> list[str] | None:
        from am.workspace import Workspace
        return Workspace.list()

    
