from pint import Quantity
from typing_extensions import cast

from am.simulator.solver.analytical import Rosenthal
from am.simulator.tool.process_map.models import ProcessMapDataPoint
from am.config import BuildParameters, Material

from .process_map_point_label import lack_of_fusion


def run_process_map_data_point(
    build_parameters: BuildParameters,
    material: Material,
    data_point: ProcessMapDataPoint,
) -> ProcessMapDataPoint:
    """
    Assigns `labels` and `melt_pool_dimensions` to process map data point.
    Right now, just support lack of fusion labeling.
    """

    model = Rosenthal(build_parameters, material)

    melt_pool_dimensions = model.solve_melt_pool_dimensions()

    hatch_spacing = cast(Quantity, build_parameters.hatch_spacing).magnitude
    layer_height = cast(Quantity, build_parameters.layer_height).magnitude

    # length = melt_pool_dimensions.length.magnitude
    width = melt_pool_dimensions.width.magnitude
    depth = melt_pool_dimensions.depth.magnitude

    labels = []
    if lack_of_fusion(hatch_spacing, layer_height, width, depth):
        labels.append("lack_of_fusion")

    # Assigns values to process map data point.
    data_point.melt_pool_dimensions = melt_pool_dimensions
    data_point.labels = labels

    return data_point
