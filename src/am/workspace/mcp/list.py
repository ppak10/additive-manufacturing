from enum import Enum

from mcp.server import FastMCP
from typing import Union

class Subfolder(str, Enum):
    meshes = "meshes"
    parts = "parts"
    segments = "segments"

def register_workspace_list(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error 
    
    @app.tool(
        title="List Workspaces",
        description="Provides a list of created workspaces.",
        structured_output=True,
    )
    def workspaces() -> ToolSuccess[list[str] | None]:
        from am.workspace.list import list_workspaces
        return tool_success(list_workspaces())

    @app.tool(
        title="List Workspace Folder",
        description="Provides a list of specific output folders created by solver within specified workspace. This includes `meshes`, `parts`, `segments`",
        structured_output=True,
    )
    def workspace_subfolder_list(
       workspace: str,
       subfolder: Subfolder
    ) -> Union[ToolSuccess[list[str] | None], ToolError]:
        """
        Lists available meshes within workspace
        """
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        outputs = None
        match subfolder:
            case Subfolder.meshes:
                from am.workspace.list import list_workspace_meshes
                outputs = list_workspace_meshes(workspace_path)
            case Subfolder.parts:
                from am.workspace.list import list_workspace_parts
                outputs = list_workspace_parts(workspace_path)
            case Subfolder.segments:
                from am.workspace.list import list_workspace_segments
                outputs = list_workspace_segments(workspace_path)
            case _:
                return tool_error(
                    "Output folder not valid",
                    "INVALID_OUTPUT_FOLDER",
                    workspace_name=workspace,
                )

        return tool_success(outputs)

    _ = ( workspaces, workspace_subfolder_list)

def register_workspace_list_resources(app: FastMCP):

    @app.resource("workspace://")
    def workspace_list() -> list[str] | None:
        from am.workspace.list import list_workspaces
        return list_workspaces()

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
            workspace_list,
            workspace_meshes_list,
            workspace_part_list,
            workspace_segments_list
        )
