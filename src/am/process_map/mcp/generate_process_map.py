from mcp.server.fastmcp import FastMCP

from typing import Union


def register_process_map_generate_process_map(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Generate Process Map",
        description="Generates a process map using the configurations in the folder and returns a list of power and velocity combinations (W and mm/s respectively) where lack of fusion is expected.",
        structured_output=True,
    )
    def process_map_generate_process_map(
        workspace: str,
        name: str | None = "default",
        # build_parameters_filename: str = "build_parameters.json",
        # material_filename: str = "material.json",
    ) -> Union[ToolSuccess[list[tuple[int, list[dict[str, int]]]]], ToolError]:
        """
        Creates a configuration file for build parameters.
        Args:
            workspace: Folder name of existing workspace.
            name: Used for the process map folder
        """

        from am.config import BuildParameters, Material
        from am.process_map.generate import generate_melt_pool_measurements
        from am.process_map.schema import ProcessMap

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        process_maps_folder = workspace_path / "process_maps"

        if name is None:
            # Get list of subdirectories sorted by modification time (newest first)
            process_map_folder = sorted(
                [d for d in process_maps_folder.iterdir() if d.is_dir()],
                key=lambda d: d.stat().st_mtime,
                reverse=True,
            )

            if not process_map_folder:
                raise FileNotFoundError(
                    f"❌ No run directories found in {process_maps_folder}"
                )

            name = process_map_folder[0].name

        try:
            workspace_path = get_workspace_path(workspace)

            # Build Parameters
            build_parameters_path = (
                # process_maps_folder / name / build_parameters_filename
                process_maps_folder
                / name
                / "build_parameters.json"
            )

            build_parameters = BuildParameters.load(build_parameters_path)

            # material_path = process_maps_folder / name / material_filename
            material_path = process_maps_folder / name / "material.json"

            material = Material.load(material_path)

            process_map_config_path = process_maps_folder / name / "config.json"

            process_map = ProcessMap.load(process_map_config_path)

            lack_of_fusion_power_velocities = generate_melt_pool_measurements(
                workspace_path=workspace_path,
                build_parameters=build_parameters,
                material=material,
                process_map=process_map,
                name=name,
                max_processes=1,
                disable_progress=True,
            )

            return tool_success(lack_of_fusion_power_velocities)

        except PermissionError as e:
            return tool_error(
                "Permission denied when generating process map.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to generate process map",
                "GENERATE_PROCESS_MAP_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = process_map_generate_process_map
