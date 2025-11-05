import matplotlib.pyplot as plt
import numpy as np
import trimesh

from datetime import datetime
from enum import Enum
from matplotlib.axes import Axes
from matplotlib.patches import Polygon
from numpy.typing import ArrayLike
from pathlib import Path
from pint import Quantity
from shapely.geometry import LineString
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
        hatch_spacing = cast(Quantity, build_parameters.hatch_spacing).to("mm")

        z_extents = self.mesh.bounds[:, 2]

        z_levels = np.arange(*z_extents, step=step.magnitude)

        sections = self.mesh.section_multiplane(
            plane_origin=self.mesh.bounds[0],
            plane_normal=[0, 0, 1],
            heights=z_levels
        )
        sections = cast(ArrayLike, sections)

        contour_out_path = toolpaths_out_path / "contour"
        contour_out_path.mkdir(exist_ok=True, parents=True)

        infill_out_path = toolpaths_out_path / "infill"
        infill_out_path.mkdir(exist_ok=True, parents=True)

        zfill = len(f"{len(sections)}")

        for section_index, section in enumerate(sections):
            if section is None:
                continue

            # Contour Plot
            axis = section.plot_discrete()
            axis = cast(Axes, axis)
            segment_index_string = f"{section_index}".zfill(zfill)
            contour_file = f"{segment_index_string}.png"
            plt.savefig(contour_out_path / contour_file)
            plt.close()

            # Infill Plot
            fig, ax = plt.subplots(figsize=(10, 10))

            # Draw perimeter and generate infill for each polygon
            for polygon in section.polygons_full:
                # Draw perimeter
                exterior_coords = np.array(polygon.exterior.coords)
                print(f"{section_index}, {exterior_coords}")
                ax.add_patch(Polygon(exterior_coords, fill=False, edgecolor='black', linewidth=2))
                
                for interior in polygon.interiors:
                    interior_coords = np.array(interior.coords)
                    ax.add_patch(Polygon(interior_coords, fill=False, edgecolor='black', linewidth=2))
                
                # Generate rectilinear infill (alternating 0°/90°)
                bounds = polygon.bounds
                is_horizontal = section_index % 2 == 0
                
                if is_horizontal:
                    # Horizontal lines
                    for y in np.arange(bounds[1], bounds[3], hatch_spacing.magnitude):
                        line = LineString([(bounds[0] - 1, y), (bounds[2] + 1, y)])
                        intersection = polygon.intersection(line)
                        self._plot_infill_line(ax, intersection)
                else:
                    # Vertical lines
                    for x in np.arange(bounds[0], bounds[2], hatch_spacing.magnitude):
                        line = LineString([(x, bounds[1] - 1), (x, bounds[3] + 1)])
                        intersection = polygon.intersection(line)
                        self._plot_infill_line(ax, intersection)
            
            ax.set_aspect('equal')
            ax.autoscale()
            
            infill_file = f"{segment_index_string}.png"
            plt.savefig(infill_out_path / infill_file, dpi=150)
            plt.close()

    def _plot_infill_line(self, ax, intersection):
        """Helper to plot infill line intersections."""
        if intersection.is_empty:
            return
        if intersection.geom_type == 'LineString':
            x, y = intersection.xy
            ax.plot(x, y, 'b-', linewidth=0.5, alpha=0.6)
        elif intersection.geom_type == 'MultiLineString':
            for geom in intersection.geoms:
                x, y = geom.xy
                ax.plot(x, y, 'b-', linewidth=0.5, alpha=0.6)


    def load_mesh(
        self,
        file_obj: Path,
        file_type: str | None = None,
        **kwargs
    ):
        self.mesh = trimesh.load_mesh(file_obj, file_type, kwargs)

