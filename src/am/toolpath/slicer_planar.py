import trimesh

from pathlib import Path

class ToolpathSlicerPlanar:
    """
    Slicer for generating planar GCode from mesh input.
    """
    
    def __init__(self):
        self.mesh: trimesh.Trimesh | None = None

    def load_mesh(
        self,
        file_obj: Path,
        file_type: str | None = None,
        **kwargs
    ):
        self.mesh = trimesh.load_mesh(file_obj, file_type, kwargs)
        print(f"self.mesh: {self.mesh}")

