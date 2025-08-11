from pathlib import Path

from am.workspace.config import WorkspaceConfig

def list_workspaces(out_path: Path | None = None) -> list[str] | None:
   """
   Lists workspace directories within out_path
   """
   if out_path is None:
       project_root = WorkspaceConfig.get_project_root_from_package()
       out_path = project_root / "out"

   if not out_path.exists() or not out_path.is_dir():
       raise FileNotFoundError

   return [
       workspace_dir.name
       for workspace_dir in out_path.iterdir()
       if workspace_dir.is_dir()
   ]

def list_workspace_meshes(workspace_path: Path) -> list[str] | None:
    """
    Lists meshes within workspace directory
    """
    meshes_path = workspace_path / "meshes"

    meshes = []
    for item in meshes_path.iterdir():
        if item.is_dir() and (item / "timesteps").is_dir():
            meshes.append(item.name)

    return meshes 

def list_workspace_parts(
        workspace_path: Path,
        suffix: str = ".gcode",
) -> list[str] | None:
    """
    Lists parts within workspace directory
    """
    parts_path = workspace_path / "parts"

    return [
        partfile.name
        for partfile in parts_path.iterdir()
        if partfile.is_file() and partfile.suffix == suffix
    ]


def list_workspace_segments(workspace_path: Path) -> list[str] | None:
    """
    Lists segments within workspace directory
    """
    segments_path = workspace_path / "segments"

    segments = []
    for item in segments_path.iterdir():
        if item.is_dir() and (item / "layers").is_dir():
            segments.append(item.name)

    return segments

