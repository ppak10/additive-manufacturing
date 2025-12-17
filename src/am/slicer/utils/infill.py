import numpy as np

from pathlib import Path
from shapely.geometry import LineString
from shapely import wkb, wkt


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

    if binary:
        infill_file = f"{index_string}.wkb"
        intersections_list = [wkb.dumps(i) for i in intersections]

        # Write as hex-encoded strings to avoid newline conflicts in binary WKB
        infill_output = [g_bytes.hex() for g_bytes in intersections_list]

    else:
        infill_file = f"{index_string}.txt"
        infill_output = [wkt.dumps(i) for i in intersections]

    infill_out_path = data_out_path / infill_file
    with open(infill_out_path, "w") as f:
        f.write("\n".join(infill_output))

    return infill_out_path
