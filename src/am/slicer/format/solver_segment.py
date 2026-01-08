import numpy as np

from pint import Quantity
from shapely import MultiLineString, LineString, Geometry
from typing_extensions import cast

from am.simulator.solver.models import SolverSegment, SolverLayer


def export_solver_layer(data_out_path, geometries, layer_index, layer_count):
    zfill = len(str(layer_count))
    solver_layer_string = f"{layer_index}".zfill(zfill)
    solver_segments = geometries_to_solver_segments(geometries)
    solver_layer = SolverLayer(
        layer_index=layer_index,
        layer_count=layer_count,
        segments=solver_segments,
    )
    solver_layer_json = solver_layer.model_dump_json(indent=2)
    solver_layer_out_path = data_out_path / f"{solver_layer_string}.json"
    with open(solver_layer_out_path, "w") as f:
        f.write(solver_layer_json)


def geometries_to_solver_segments(
    geometries: list[Geometry],
    max_segment_length: float = 0.1,  # 0.1 mm
    units="mm",
    verbose=False,
) -> list[SolverSegment]:
    """
    Converts geometries from slice to solver segments (assumes mm)
    Supports LineString and MultiLineString geometries.
    """
    solver_segments = []

    for geometry_index, geometry in enumerate(geometries):

        # Skip non-LineString geometries (e.g., POINTs)
        if not isinstance(geometry, (LineString, MultiLineString)):
            # print(f"Warning: Skipping non-LineString geometry: {geometry.geom_type}")
            continue

        # Convert MultiLineString to list of LineStrings, or wrap single LineString in list
        if isinstance(geometry, MultiLineString):
            linestrings = list(geometry.geoms)
        else:
            linestrings = [geometry]

        # Process each LineString
        for linestring_index, linestring in enumerate(linestrings):
            start = 0
            travel = True

            # Skip invalid LineStrings with less than 2 points
            if len(linestring.coords) < 2:
                if verbose:
                    print(
                        f"Warning: Skipping invalid LineString with {len(linestring.coords)} point(s)"
                    )
                continue

            # Skip degenerate LineStrings where all points are the same
            if linestring.length == 0:
                if verbose:
                    print(
                        f"Warning: Skipping degenerate LineString with zero length at {linestring.coords[0]}"
                    )
                continue

            segmentized_geometries = linestring.segmentize(max_segment_length)
            # print(len(geometries), segmentized_geometries)

            x_values, y_values = segmentized_geometries.xy

            # X and Y values length should always be the same, but just in case
            segments_length = min(len(x_values), len(y_values))

            if segments_length > 0:

                if geometry_index == 0 and linestring_index == 0:
                    # Manually set the prev x and y for the first geometry.
                    prev_x, prev_y = x_values[0], y_values[0]
                    travel = False
                    start = 1

                for segment_index in range(start, segments_length):
                    x, y = x_values[segment_index], y_values[segment_index]
                    dx, dy = x - prev_x, y - prev_y
                    distance = (dx**2 + dy**2) ** 0.5

                    angle = np.arctan2(dy, dx)

                    solver_segment = SolverSegment(
                        x1=cast(Quantity, Quantity(prev_x, units)),
                        y1=cast(Quantity, Quantity(prev_y, units)),
                        x2=cast(Quantity, Quantity(x, units)),
                        y2=cast(Quantity, Quantity(y, units)),
                        angle=cast(Quantity, Quantity(angle, "radians")),
                        distance=cast(Quantity, Quantity(distance, units)),
                        travel=travel,
                    )

                    prev_x, prev_y = x, y
                    travel = False

                    solver_segments.append(solver_segment)

    return solver_segments
