import shutil
from pathlib import Path

from wa.models import Workspace, WorkspaceFolder
from wa.workspace.create import create_workspace, create_workspace_folder

from am.config import BuildParameters, Material, MeshParameters


def create_additive_manufacturing_workspace(
    workspace_name: str,
    workspaces_path: Path | None = None,
    force: bool = False,
    include_examples: bool = False,
    **kwargs,
) -> Workspace:
    """
    Create Additive Manufacutring Workspace class object and folder.
    """

    # Creates workspace folder
    workspace = create_workspace(
        workspace_name=workspace_name, workspaces_path=workspaces_path, force=force
    )

    # Creates config folder
    create_workspace_configs_folder(
        workspace_name=workspace_name, workspaces_path=workspaces_path, force=force
    )

    create_workspace_parts_folder(
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
        include_examples=include_examples,
    )

    return workspace


def create_workspace_parts_folder(
    workspace_name: str,
    workspaces_path: Path | None = None,
    force: bool = False,
    include_examples: bool = False,
) -> WorkspaceFolder:
    """
    Create parts subfolder within workspace.
    """

    # Create parts directory
    parts_folder = create_workspace_folder(
        workspace_folder_name="parts",
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )

    if include_examples:
        # Get the data/parts directory
        from am.data import DATA_DIR

        data_parts_dir = DATA_DIR / "parts"

        # Copy all files from data/parts to workspace/parts
        for file_path in data_parts_dir.iterdir():
            dest_path = parts_folder.path / file_path.name
            shutil.copy2(file_path, dest_path)

    return parts_folder


def create_workspace_configs_folder(
    workspace_name: str,
    workspaces_path: Path | None = None,
    force: bool = False,
) -> WorkspaceFolder:
    """
    Initialize configs subfolder within workspace with defaults.
    """

    configs_folder = create_workspace_folder(
        workspace_folder_name="configs",
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )

    build_parameters = BuildParameters()
    build_parameters_folder = create_workspace_folder(
        workspace_folder_name=["configs", "build_parameters"],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )
    build_parameters_path = build_parameters_folder.path / "default.json"
    _ = build_parameters.save(build_parameters_path)

    material = Material()
    material_folder = create_workspace_folder(
        workspace_folder_name=["configs", "material"],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )
    material_path = material_folder.path / "default.json"
    _ = material.save(material_path)

    mesh_parameters = MeshParameters()
    mesh_parameters_folder = create_workspace_folder(
        workspace_folder_name=["configs", "mesh_parameters"],
        workspace_name=workspace_name,
        workspaces_path=workspaces_path,
        force=force,
    )
    mesh_parameters_path = mesh_parameters_folder.path / "default.json"
    _ = mesh_parameters.save(mesh_parameters_path)

    return configs_folder
