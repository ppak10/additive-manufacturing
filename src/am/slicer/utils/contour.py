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
