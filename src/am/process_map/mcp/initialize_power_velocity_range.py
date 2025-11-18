from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_process_map_initialize_power_velocity_range(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Initialize Process Map with Power and Velocity Range",
        description="Creates the folder for process map configuration for a range of power and velocity build parameters",
        structured_output=True,
    )
    async def process_map_initialize_power_velocity_range(
        workspace: str,
        name: str | None = "default",
        build_parameters_filename: str = "default.json",
        material_filename: str = "default.json",
        beam_power_range: list[int] = [100, 1100, 100],
        beam_power_units: str = "W",
        scan_velocity_range: list[int] = [100, 1100, 100],
        scan_velocity_units: str = "mm/s",
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Creates a configuration file for build parameters.
        Args:
            workspace: Folder name of existing workspace.
            name: Used for the process map folder
        """

        from am.config import BuildParameters, Material
        from am.process_map.initialize import initialize_power_velocity_range

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace)

            # Build Parameters
            build_parameters_path = (
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            build_parameters = BuildParameters.load(build_parameters_path)

            material_path = workspace_path / "config" / "materials" / material_filename
            material = Material.load(material_path)

            out_path = initialize_power_velocity_range(
                workspace_path=workspace_path,
                build_parameters=build_parameters,
                material=material,
                name=name,
                beam_power_range=beam_power_range,
                beam_power_units=beam_power_units,
                scan_velocity_range=scan_velocity_range,
                scan_velocity_units=scan_velocity_units,
            )

            return tool_success(out_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when initializing process map.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create process map folder",
                "INITIALIZE_PROCESS_MAP_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = process_map_initialize_power_velocity_range
