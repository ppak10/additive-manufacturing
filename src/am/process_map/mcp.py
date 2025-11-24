from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_process_map(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    from am.process_map.plot import PlotType

    @app.tool(
        title="Process Map",
        description="Generate a process map from a combination of build parameters and material",
        structured_output=True,
    )
    async def process_map(
        process_map_folder_name: str,
        build_parameters_file_name: str,
        material_file_name: str,
        process_map_file_name: str,
        plot_type: PlotType,
        workspace_name: str,
        workspaces_path: Path | None = None,
        force: bool = False,
        num_proc: int = 1,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Initialize additive manufacturing workspace folder with relevant subfolders.

        Args:
            process_map_folder_name: Name that describes the process map
            build_parameters_file_name: Build parameters config file name
            material_file_name: Material configuration file name
            process_map_file_name: Process map configuration file name
            workspace_name: Name of folder to initialize.
            workspaces_path: Path of folder containing workspaces.
            force: Overwrite existing workspace.
            include_examples: Copies examples to workspace folder.
        """
        from am.process_map.create import create_process_map_folder
        from am.process_map.plot import plot_process_map
        from am.process_map.run import run_process_map
        from am.process_map.utils import process_map_points_to_plot_data
        from am.config import BuildParameters, Material, ProcessMap

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace_name)

            build_parameters = BuildParameters.load(
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_file_name
            )
            material = Material.load(
                workspace_path / "configs" / "materials" / material_file_name
            )
            process_map = ProcessMap.load(
                workspace_path / "configs" / "process_maps" / process_map_file_name
            )

            process_map_folder = create_process_map_folder(
                process_map_folder_name=process_map_folder_name,
                build_parameters=build_parameters,
                material=material,
                process_map=process_map,
                workspace_name=workspace_name,
                workspaces_path=workspaces_path,
                force=force,
            )

            process_map_points = run_process_map(
                build_parameters=build_parameters,
                material=material,
                process_map=process_map,
                process_map_path=process_map_folder.path,
                num_proc=num_proc,
            )

            plot_data = process_map_points_to_plot_data(process_map_points)

            plot_process_map(
                process_map_path=process_map_folder.path,
                plot_data=plot_data,
                plot_type=plot_type,
            )

            return tool_success(workspace_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating process map",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to generate process map",
                "PROCESS_MAP_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = process_map
