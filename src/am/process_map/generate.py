import asyncio
import multiprocessing as mp
import numpy as np
import sys

from copy import deepcopy
from pathlib import Path
from pint import Quantity
from tqdm import tqdm

from am.config import BuildParameters, Material
from am.solver.model import Rosenthal

from .classification import lack_of_fusion
from .schema import ProcessMap
from .plot import create_lack_of_fusion_plot


def process_layer_height_offset(
    layer_height_offset: int,
    workspace_path: Path,
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    prescribed_layer_height: float,
    process_id: int = 0,  # Add process ID for unique progress bars
    disable_progress: bool = False,
) -> tuple[int, list[dict[str, int]], np.ndarray, list, list]:
    """
    Process a single layer height offset in a separate process.
    Returns: (layer_height, lack_of_fusion_list, lack_of_fusion_2d, x_values, y_values)
    """
    # Create a deep copy to avoid race conditions
    local_build_parameters = deepcopy(build_parameters)

    parameters = process_map.parameters
    point_tuples = []
    length_2d = []
    length_row = []
    width_2d = []
    width_row = []
    depth_2d = []
    depth_row = []
    x_values = []
    y_values = []

    # Create unique progress bar with position
    desc = f"Layer {layer_height_offset:+3d}μm"

    for point in tqdm(
        process_map.points,
        desc=desc,
        position=process_id,  # Each process gets its own line
        leave=True,
        file=sys.stdout,
        ncols=100,  # Fixed width to prevent overlap
        disable=disable_progress,  # Can be controlled externally
    ):
        parameter_tuple = ()
        x, y = point[1].magnitude, point[0].magnitude
        if x not in x_values:
            x_values.append(x)
        if y not in y_values:
            if len(y_values) != 0:
                length_2d.append(length_row)
                length_row = []
                depth_2d.append(depth_row)
                depth_row = []
                width_2d.append(width_row)
                width_row = []
            y_values.append(y)

        for index, parameter in enumerate(parameters):
            local_build_parameters.__setattr__(parameter, point[index])
            parameter_tuple = parameter_tuple + (point[index].magnitude,)

        layer_height = prescribed_layer_height + layer_height_offset
        local_build_parameters.layer_height = Quantity(layer_height, "microns")
        model = Rosenthal(local_build_parameters, material)
        melt_pool_dimensions = model.solve_melt_pool_dimensions()

        point_tuples.append((parameter_tuple, melt_pool_dimensions))
        depth_row.append(melt_pool_dimensions.depth.magnitude)
        width_row.append(melt_pool_dimensions.width.magnitude)
        length_row.append(melt_pool_dimensions.length.magnitude)

    # Add last rows
    depth_2d.append(depth_row)
    length_2d.append(length_row)
    width_2d.append(width_row)

    lack_of_fusion_2d = lack_of_fusion(
        local_build_parameters.hatch_spacing.magnitude,
        local_build_parameters.layer_height.magnitude,
        np.array(width_2d),
        np.array(depth_2d),
    )

    # Generate lack of fusion list
    lack_of_fusion_list = []
    for row_index, row in enumerate(lack_of_fusion_2d):
        for col_index, col in enumerate(row):
            if col:
                lack_of_fusion_list.append(
                    {
                        "power": y_values[row_index],
                        "velocity": x_values[col_index],
                    }
                )

    actual_layer_height = prescribed_layer_height + layer_height_offset

    return (
        actual_layer_height,
        lack_of_fusion_list,
        lack_of_fusion_2d,
        x_values,
        y_values,
    )


async def generate_melt_pool_measurements_async(
    workspace_path: Path,
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    name: str,
    max_processes: int | None = None,
    disable_progress=True,
) -> list[tuple[int, dict[str, int]]]:
    """
    Async version of generate_melt_pool_measurements.
    """
    return await asyncio.get_event_loop().run_in_executor(
        None,
        generate_melt_pool_measurements,
        workspace_path,
        build_parameters,
        material,
        process_map,
        name,
        max_processes,
        disable_progress,
    )


def generate_melt_pool_measurements(
    workspace_path: Path,
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    name: str,
    max_processes: int | None = None,
    disable_progress: bool = False,
) -> list[tuple[int, dict[str, int]]]:
    """
    Generate process map with optional multiprocessing.
    If max_processes=1, runs sequentially without multiprocessing overhead.
    """
    if max_processes is None:
        max_processes = min(3, mp.cpu_count())

    prescribed_layer_height = build_parameters.layer_height.to("microns").magnitude
    layer_height_offsets = [-25, 0, 25]

    # Sequential processing for max_processes=1 or compatibility issues
    if max_processes == 1:
        print("🔄 Running in sequential mode (no multiprocessing)")

        results = []
        for i, offset in enumerate(layer_height_offsets):
            print(f"⏳ Processing layer height offset: {offset:+d}μm ({i+1}/3)")

            result = process_layer_height_offset(
                offset,
                workspace_path,
                build_parameters,
                material,
                process_map,
                prescribed_layer_height,
                0,  # Single process ID
                disable_progress,
            )
            results.append(result)
            print(f"✅ Completed layer height offset: {offset:+d}μm")

        print("🎉 All processing completed successfully!")

    else:
        # Multiprocessing version
        print(f"🚀 Starting multiprocessing with {max_processes} processes")
        print(f"💻 System has {mp.cpu_count()} CPU cores available")
        print("📊 Progress bars (one per process):")
        print()  # Add space for progress bars

        import concurrent.futures

        # Use ProcessPoolExecutor for better control over individual processes
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_processes
        ) as executor:
            # Submit all jobs with process IDs for unique progress bar positions
            future_to_info = {}
            for i, offset in enumerate(layer_height_offsets):
                future = executor.submit(
                    process_layer_height_offset,
                    offset,
                    workspace_path,
                    build_parameters,
                    material,
                    process_map,
                    prescribed_layer_height,
                    i,  # Process ID for progress bar positioning
                )
                future_to_info[future] = (offset, i)

            # Collect results as they complete
            results = []
            completed = 0
            total = len(layer_height_offsets)

            for future in concurrent.futures.as_completed(future_to_info):
                offset, process_id = future_to_info[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    # Print completion message after progress bars
                    print(
                        f"\n✅ Process {process_id + 1}/3 (offset {offset:+d}μm) completed!"
                    )
                except Exception as exc:
                    print(f"\n❌ Process for offset {offset} failed: {exc}")

        print(f"\n🎉 All {completed} processes completed successfully!")

    # Sort and process results (same for both modes)
    results.sort(key=lambda x: x[0])
    lack_of_fusion_lists = [(r[0], r[1]) for r in results]
    lack_of_fusion_2ds = [(r[0], r[2]) for r in results]
    x_values = results[0][3]
    y_values = results[0][4]

    create_lack_of_fusion_plot(
        data_2ds=lack_of_fusion_2ds,
        x_values=x_values,
        y_values=y_values,
        save_path=workspace_path / "process_maps" / name / "lack_of_fusion.png",
        title=None,
        xlabel="Scanning Velocity (mm/s)",
        ylabel="Beam Power (W)",
        is_boolean=True,
        colorbar_label="Layer Height",
        transparent_bg=True,
    )

    return lack_of_fusion_lists
