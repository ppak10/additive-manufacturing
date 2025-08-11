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

    
    @app.tool(
        title="List Workspaces",
        description="Provides a list of created workspaces.",
        structured_output=True,
    )
    def workspaces() -> list[str] | None:
        from am.workspace.list import list_workspaces
        return list_workspaces()

    @app.resource("workspace://")
    def workspace_list() -> list[str] | None:
        from am.workspace.list import list_workspaces
        return list_workspaces()

    @app.tool(
        title="List Workspace Meshes",
        description="Provides a list of mesh folders created by solver within specified workspace",
        structured_output=True,
    )
    def workspace_meshes(workspace: str) -> list[str] | None:
        """
        Lists available meshes within workspace
        """
        from am.workspace.list import list_workspace_meshes
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_meshes = list_workspace_meshes(workspace_path)

        return workspace_meshes

    @app.resource("workspace://{workspace}/meshes")
    def workspace_meshes_list(workspace: str) -> list[str] | None:
        """
        Lists available meshes within workspace
        """
        from am.workspace.list import list_workspace_meshes
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_meshes = list_workspace_meshes(workspace_path)

        return workspace_meshes

    @app.tool(
        title="List Workspace Parts",
        description="Provides a list of parts within specified workspace",
        structured_output=True,
    )
    def workspace_parts(workspace: str) -> list[str] | None:
        """
        Lists available parts within workspace
        """
        from am.workspace.list import list_workspace_parts
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_parts = list_workspace_parts(workspace_path)

        return workspace_parts

    @app.resource("workspace://{workspace}/part")
    def workspace_part_list(workspace: str) -> list[str] | None:
        """
        Lists available parts within workspace
        """
        from am.workspace.list import list_workspace_parts
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_parts = list_workspace_parts(workspace_path)

        return workspace_parts

    @app.tool(
        title="List Workspace Segments",
        description="Provides a list of segments folders within specified workspace",
        structured_output=True,
    )
    def workspace_segments(workspace: str) -> list[str] | None:
        """
        Lists available segments within workspace
        """
        from am.workspace.list import list_workspace_segments
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_segments = list_workspace_segments(workspace_path)

        return workspace_segments

    @app.resource("workspace://{workspace}/segments")
    def workspace_segments_list(workspace: str) -> list[str] | None:
        """
        Lists available segments within workspace
        """
        from am.workspace.list import list_workspace_segments
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_segments = list_workspace_segments(workspace_path)

        return workspace_segments

    _ = (
            workspace_initialize,
            workspaces,
            workspace_list,
            workspace_meshes,
            workspace_meshes_list,
            workspace_parts,
            workspace_part_list,
            workspace_segments,
            workspace_segments_list
        )

