import warnings

from copy import deepcopy
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from pint import Quantity
from typing import cast
from tqdm.rich import tqdm

from am.config import BuildParameters, Material, ProcessMap
from am.solver.model import Rosenthal

from .classification import lack_of_fusion
from .models import MeltPoolClassifications, ProcessMapPoint, ProcessMapPoints

# Suppress tqdm experimental warning for rich integration
warnings.filterwarnings("ignore", message=".*rich is experimental.*")


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


def run_process_map(
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    process_map_path: Path,
    # model_name: str = "rosenthal",
    num_proc: int = 1,
) -> ProcessMapPoints:
    points = []

    if num_proc <= 1:

        # Iterates through points z (inner) -> y (middle) -> x (outer)
        for point in tqdm(process_map.points, desc="Running simulations"):
            # Copies build parameters to a new object to pass as overrides.
            modified_build_parameters = deepcopy(build_parameters)

            for index, parameter in enumerate(process_map.parameters):
                modified_build_parameters.__setattr__(parameter, point[index])

            point = run_process_map_point(modified_build_parameters, material)

            points.append(point)
    else:
        # Multi-process execution
        args_list = []

        for point in process_map.points:
            # Copies build parameters to a new object to pass as overrides.
            modified_build_parameters = deepcopy(build_parameters)

            for index, parameter in enumerate(process_map.parameters):
                modified_build_parameters.__setattr__(parameter, point[index])

            args = (modified_build_parameters, material)
            args_list.append(args)

        with ProcessPoolExecutor(max_workers=num_proc) as executor:
            futures = []
            for args in args_list:
                future = executor.submit(run_process_map_point, *args)
                futures.append(future)

            # Use tqdm to track progress
            for future in tqdm(
                as_completed(futures), total=len(futures), desc="Running simulations"
            ):
                result = future.result()  # This will raise any exceptions that occurred
                points.append(result)

    process_map_points = ProcessMapPoints(points=points)

    process_map_points.save(process_map_path / "points.json")

    return process_map_points
