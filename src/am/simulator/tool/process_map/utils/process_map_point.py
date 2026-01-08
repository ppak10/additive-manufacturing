from am.simulator.process_map.models import ProcessMapPoint
from am.config import BuildParameters, Material

from .process_map_point_label import lack_of_fusion


def run_process_map_point(
    build_parameters: BuildParameters, material: Material
) -> ProcessMapPoint:

    # if model_name == "rosenthal":
    model = Rosenthal(build_parameters, material)

    melt_pool_dimensions = model.solve_melt_pool_dimensions()

    hatch_spacing = cast(Quantity, build_parameters.hatch_spacing).magnitude
    layer_height = cast(Quantity, build_parameters.layer_height).magnitude

    # length = melt_pool_dimensions.length.magnitude
    width = melt_pool_dimensions.width.magnitude
    depth = melt_pool_dimensions.depth.magnitude

    melt_pool_classifications = MeltPoolClassifications(
        lack_of_fusion=lack_of_fusion(hatch_spacing, layer_height, width, depth)
    )

    process_map_point = ProcessMapPoint(
        build_parameters=build_parameters,
        melt_pool_dimensions=melt_pool_dimensions,
        melt_pool_classifications=melt_pool_classifications,
    )

    return process_map_point
