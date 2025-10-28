import matplotlib.pyplot as plt
import numpy as np
import trimesh

from datetime import datetime
from enum import Enum
from matplotlib.axes import Axes
from numpy.typing import ArrayLike
from pathlib import Path
from pint import Quantity
from typing import cast

from am.schema import BuildParameters

class ToolpathOutputFolder(str, Enum):
    toolpaths = "toolpaths"

class ToolpathSlicerPlanar:
    """
    Slicer for generating planar GCode from mesh input.
    """
    
    def __init__(self):
        self.mesh: trimesh.Trimesh | None = None

    def slice(
        self,
        build_parameters: BuildParameters,
        workspace_path: Path,
        run_name: str | None = None,
    ):

        # Creates run folder inside workspace for slicer runs.
        if run_name is None:
            run_name = datetime.now().strftime("slicer_planar_%Y%m%d_%H%M%S")

        toolpaths_out_path = workspace_path / "toolpaths" / run_name
        toolpaths_out_path.mkdir(exist_ok=True, parents=True)

        # Save solver configs
        build_parameters.save(toolpaths_out_path / "config" / "build_parameters.json")

        if self.mesh is None:
            return None

        step = cast(Quantity, build_parameters.layer_height).to("mm")

        z_extents = self.mesh.bounds[:, 2]

        z_levels = np.arange(*z_extents, step=step.magnitude)

        sections = self.mesh.section_multiplane(
            plane_origin=self.mesh.bounds[0],
            plane_normal=[0, 0, 1],
            heights=z_levels
        )
        sections = cast(ArrayLike, sections)

        slices_out_path = toolpaths_out_path / "slices"
        slices_out_path.mkdir(exist_ok=True, parents=True)

        zfill = len(f"{len(sections)}")

        for section_index, section in enumerate(sections):
            axis = section.plot_discrete()
            axis = cast(Axes, axis)
            segment_index_string = f"{section_index}".zfill(zfill)
            slice_file = f"{segment_index_string}.png"
            slice_out_path = slices_out_path / slice_file
            plt.savefig(slice_out_path)
            plt.close()

    def load_mesh(
        self,
        file_obj: Path,
        file_type: str | None = None,
        **kwargs
    ):
        self.mesh = trimesh.load_mesh(file_obj, file_type, kwargs)

