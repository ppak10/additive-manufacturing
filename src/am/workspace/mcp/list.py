from mcp.server import FastMCP

def register_workspace_list(app: FastMCP):
    from am.mcp.types import ToolSuccess
    from am.mcp.utils import tool_success
    
    @app.tool(
        title="List Workspaces",
        description="Provides a list of created workspaces.",
        structured_output=True,
    )
    def workspaces() -> ToolSuccess[list[str] | None]:
        from am.workspace.list import list_workspaces
        return tool_success(list_workspaces())

    @app.resource("workspace://")
    def workspace_list() -> list[str] | None:
        from am.workspace.list import list_workspaces
        return list_workspaces()

    @app.tool(
        title="List Workspace Meshes",
        description="Provides a list of mesh folders created by solver within specified workspace",
        structured_output=True,
    )
    def workspace_meshes(
       workspace: str
    ) -> ToolSuccess[list[str] | None]:
        """
        Lists available meshes within workspace
        """
        from am.workspace.list import list_workspace_meshes
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_meshes = list_workspace_meshes(workspace_path)

        return tool_success(workspace_meshes)

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
    def workspace_parts(
        workspace: str
    ) -> ToolSuccess[list[str] | None]:
        """
        Lists available parts within workspace
        """
        from am.workspace.list import list_workspace_parts
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_parts = list_workspace_parts(workspace_path)

        return tool_success(workspace_parts)

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
    def workspace_segments(
        workspace: str
    ) -> ToolSuccess[list[str] | None]:
        """
        Lists available segments within workspace
        """
        from am.workspace.list import list_workspace_segments
        from am.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)
        workspace_segments = list_workspace_segments(workspace_path)

        return tool_success(workspace_segments)

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
            workspaces,
            workspace_list,
            workspace_meshes,
            workspace_meshes_list,
            workspace_parts,
            workspace_part_list,
            workspace_segments,
            workspace_segments_list
        )

