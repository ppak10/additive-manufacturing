import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import LineString
from shapely import wkb, wkt


def contour_generate(
    section,
    hatch_spacing,  # TODO: Implement multicontours and respect infill.
    data_out_path,
    index_string,
    binary: bool = True,
) -> Path | None:
    """Process a single section for contour generation."""
    if section is None:
        return None

    perimeters = []

    for polygon in section.polygons_full:
        # Save exterior (outside perimeter) as LineString
        exterior_coords = list(polygon.exterior.coords)
        perimeters.append(LineString(exterior_coords))

        # Save interiors (inside perimeters) as LineStrings
        for interior in polygon.interiors:
            interior_coords = list(interior.coords)
            perimeters.append(LineString(interior_coords))

    if binary:
        perimeters_list = [wkb.dumps(p) for p in perimeters]
        contour_output = [g_bytes.hex() for g_bytes in perimeters_list]
        contour_file = f"{index_string}.wkb"

    else:
        contour_output = [wkt.dumps(p) for p in perimeters]
        contour_file = f"{index_string}.txt"

    contour_out_path = data_out_path / contour_file
    with open(contour_out_path, "w") as f:
        f.write("\n".join(contour_output))

    return contour_out_path


def contour_visualization(contour_file, binary, mesh_bounds, contour_images_out_path):
    """Process a single contour file for visualization."""

    # Read geometries from file
    perimeters = []

    if binary:
        # WKB files are hex-encoded to avoid newline conflicts in binary data
        with open(contour_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        g_bytes = bytes.fromhex(line)
                        perimeters.append(wkb.loads(g_bytes))
                    except Exception as e:
                        # Skip malformed geometries
                        print(
                            f"Warning: Skipping malformed geometry in {contour_file.name}: {e}"
                        )
    else:
        with open(contour_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    perimeters.append(wkt.loads(line))

    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot all contour lines
    for perimeter in perimeters:
        if perimeter.is_empty:
            return
        if perimeter.geom_type == "LineString":
            x, y = perimeter.xy
            ax.plot(x, y, "g-", linewidth=1.5, alpha=0.8)
        elif perimeter.geom_type == "MultiLineString":
            for geom in perimeter.geoms:
                x, y = geom.xy
                ax.plot(x, y, "g-", linewidth=1.5, alpha=0.8)

    # Set consistent bounds across all layers using mesh bounds
    ax.set_xlim(0, abs(mesh_bounds[0, 0]) + abs(mesh_bounds[1, 0]))
    ax.set_ylim(0, abs(mesh_bounds[0, 1]) + abs(mesh_bounds[1, 1]))
    ax.set_aspect("equal")

    # Save image with same base name as data file
    image_file = contour_file.stem + ".png"
    plt.savefig(contour_images_out_path / image_file, dpi=150)
    plt.close()

    return contour_file.name
