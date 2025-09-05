import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path
from tqdm import tqdm

from am.schema import BuildParameters, Material
from am.solver.model import Rosenthal

from .classification import balling, lack_of_fusion, keyhole
from .schema import ProcessMap


# TODO: Make better
def generate_melt_pool_measurements(
    workspace_path: Path,
    build_parameters: BuildParameters,
    material: Material,
    process_map: ProcessMap,
    name: str,
) -> list[dict[str, int]]:
    """
    Function to generate process map with provided configurations.
    Right now assumes the beam_power and scan_velocity are two parameters.
    Also generates the visuals and stuff, will move this elsewhere later.
    """

    parameters = process_map.parameters

    # i.e. [((100, 100), <measurements>), ((100, 150), <measurements>)]
    point_tuples = []

    length_2d = []
    length_row = []

    width_2d = []
    width_row = []

    depth_2d = []
    depth_row = []

    x_values = []
    y_values = []

    for point in tqdm(process_map.points):

        parameter_tuple = ()

        # scanning_velocity, beam_power
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
            build_parameters.__setattr__(parameter, point[index])
            parameter_tuple = parameter_tuple + (point[index].magnitude,)

        model = Rosenthal(build_parameters, material)

        # TODO: Create a schema for saving measurements. Probably put this
        # inside a schema related to process maps.
        melt_pool_dimensions = model.solve_melt_pool_dimensions()
        point_tuples.append((parameter_tuple, melt_pool_dimensions))
        depth_row.append(melt_pool_dimensions.depth.magnitude)
        width_row.append(melt_pool_dimensions.width.magnitude)
        length_row.append(melt_pool_dimensions.length.magnitude)

    # Add last
    depth_2d.append(depth_row)
    length_2d.append(length_row)
    width_2d.append(width_row)

    keyhole_2d = keyhole(np.array(width_2d), np.array(depth_2d))
    lack_of_fusion_2d = lack_of_fusion(
        build_parameters.hatch_spacing.magnitude,
        build_parameters.layer_height.magnitude,
        np.array(width_2d),
        np.array(depth_2d),
    )
    balling_2d = balling(np.array(length_2d), np.array(width_2d))

    # Depth plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        depth_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    fig.colorbar(im, ax=ax, label="microns")
    ax.set_title("Melt Pool Depth")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "depth.png")
    plt.close(fig)

    # Width plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        width_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    fig.colorbar(im, ax=ax, label="microns")
    ax.set_title("Melt Pool Width")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "width.png")
    plt.close(fig)

    # Length plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        length_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    fig.colorbar(im, ax=ax, label="microns")
    ax.set_title("Melt Pool Length")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "length.png")
    plt.close(fig)

    # Keyhole plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        keyhole_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    ax.set_title("Keyholing")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "keyhole.png")
    plt.close(fig)

    # Lack of Fusion plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        lack_of_fusion_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    ax.set_title("Lack of Fusion")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "lack_of_fusion.png")
    plt.close(fig)

    # Balling plot
    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(
        balling_2d,
        cmap="viridis",
        origin="lower",
        extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
    )
    fig.colorbar(im, ax=ax, label="microns")
    ax.set_title("Balling")
    ax.set_xlabel("scanning_velocity (mm/s)")
    ax.set_ylabel("beam_power (W)")
    plt.savefig(workspace_path / "process_maps" / name / "balling.png")
    plt.close(fig)

    # Lack of Fusion values
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

    return lack_of_fusion_list
