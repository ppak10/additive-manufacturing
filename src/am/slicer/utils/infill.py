import matplotlib.pyplot as plt
import numpy as np

from shapely.geometry import LineString
from shapely import wkb, wkt


# Helper functions for multiprocessing
def infill_generate(
    section,
    section_index,
    hatch_spacing,
    infill_data_out_path,
    infill_index_string,
    binary,
):
    """Process a single section for infill generation."""
    if section is None:
        return None

    intersections = []

    for polygon in section.polygons_full:
        # Generate rectilinear infill (alternating 0°/90°)
        bounds = polygon.bounds
        is_horizontal = section_index % 2 == 0

        if is_horizontal:
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
        intersections_list = [wkb.dumps(i) for i in intersections]
        infill_file = f"{infill_index_string}.wkb"

        # Write as hex-encoded strings to avoid newline conflicts in binary WKB
        with open(infill_data_out_path / infill_file, "w") as f:
            hex_strings = [g_bytes.hex() for g_bytes in intersections_list]
            f.write("\n".join(hex_strings))
    else:
        intersections_list = [wkt.dumps(i) for i in intersections]
        infill_file = f"{infill_index_string}.txt"

        with open(infill_data_out_path / infill_file, "w") as f:
            f.write("\n".join(intersections_list))

    return section_index


def infill_visualization(infill_file, binary, mesh_bounds, infill_images_out_path):
    """Process a single infill file for visualization."""

    # Read geometries from file
    intersections = []

    if binary:
        # WKB files are hex-encoded to avoid newline conflicts in binary data
        with open(infill_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        g_bytes = bytes.fromhex(line)
                        intersections.append(wkb.loads(g_bytes))
                    except Exception as e:
                        # Skip malformed geometries
                        print(
                            f"Warning: Skipping malformed geometry in {infill_file.name}: {e}"
                        )
    else:
        with open(infill_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    intersections.append(wkt.loads(line))

    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot all infill lines
    for intersection in intersections:
        if intersection.is_empty:
            return
        if intersection.geom_type == "LineString":
            x, y = intersection.xy
            ax.plot(x, y, "b-", linewidth=0.5, alpha=0.6)
        elif intersection.geom_type == "MultiLineString":
            for geom in intersection.geoms:
                x, y = geom.xy
                ax.plot(x, y, "b-", linewidth=0.5, alpha=0.6)

    # Set consistent bounds across all layers using mesh bounds
    ax.set_xlim(0, abs(mesh_bounds[0, 0]) + abs(mesh_bounds[1, 0]))
    ax.set_ylim(0, abs(mesh_bounds[0, 1]) + abs(mesh_bounds[1, 1]))
    ax.set_aspect("equal")

    # Save image with same base name as data file
    image_file = infill_file.stem + ".png"
    plt.savefig(infill_images_out_path / image_file, dpi=150)
    plt.close()

    return infill_file.name
