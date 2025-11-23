from pathlib import Path

from am.config import BuildParameters, Material, ProcessMap

from wa.models import WorkspaceFolder
from wa.workspace.create import create_workspace_folder


def create_process_map_folder(
    process_map_folder_name: str,
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    workspace_name: str,
    workspaces_path: Path | None = None,
    force: bool = False,
) -> WorkspaceFolder:
    """
    Creates process map subfolder within workspace process maps folder.
    Also initializes the configuration files within the process map folder.
    """

    # Process Map subfolder
    process_map_folder = create_workspace_folder(
        workspace_folder_name=["process_maps", process_map_folder_name],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )

    # Process Map Config subfolder
    process_map_config_folder = create_workspace_folder(
        workspace_folder_name=["process_maps", process_map_folder_name, "config"],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )

    build_parameters.save(process_map_config_folder.path / "build_parameters.json")
    material.save(process_map_config_folder.path / "material.json")
    process_map.save(process_map_config_folder.path / "process_map.json")

    # Process Map Plots subfolder
    create_workspace_folder(
        workspace_folder_name=["process_maps", process_map_folder_name, "plots"],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )

    return process_map_folder
