import numpy as np

from pathlib import Path
from shapely.geometry import LineString

from am.slicer.utils.geometry import save_geometries


# Helper functions for multiprocessing
def infill_rectilinear(
    section,
    horizontal,
    hatch_spacing,
    data_out_path,
    index_string,
    binary: bool = True,
) -> Path | None:
    """
    Process to generate alternating rectilinear infill for a single section.
    """

    if section is None:
        return None

    intersections = []

    for polygon in section.polygons_full:
        # Generate rectilinear infill (alternating 0°/90°)
        bounds = polygon.bounds

        if horizontal:
            # Horizontal lines
            for y in np.arange(bounds[1], bounds[3], hatch_spacing):
                line = LineString([(bounds[0] - 1, y), (bounds[2] + 1, y)])
                intersections.append(polygon.intersection(line))
        else:
            # Vertical lines
            for x in np.arange(bounds[0], bounds[2], hatch_spacing):
                line = LineString([(x, bounds[1] - 1), (x, bounds[3] + 1)])
                intersections.append(polygon.intersection(line))

    out_path = data_out_path / f"{index_string}{'.wkb' if binary else '.txt'}"

    return save_geometries(intersections, out_path, binary)
