from pathlib import Path
from shapely.geometry import LineString

from am.slicer.utils.geometry import save_geometries


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

    out_path = data_out_path / f"{index_string}{'.wkb' if binary else '.txt'}"

    return save_geometries(perimeters, out_path, binary)
