from pathlib import Path
from pint import Quantity

from am.config import BuildParameters, Material
from .schema import ProcessMap


def initialize_power_velocity_range(
    workspace_path: Path,
    build_parameters: BuildParameters,
    material: Material,
    name: str | None = None,
    beam_power_range: list[int] = [100, 1100, 100],
    beam_power_units: str = "W",
    scan_velocity_range: list[int] = [100, 1100, 100],
    scan_velocity_units: str = "mm/s",
) -> Path:
    """
    Function to initialize process map for common configurations.
    """

    if len(beam_power_range) == 1:
        beam_power_min = 0
        beam_power_max = beam_power_range[0]
    else:
        beam_power_min = beam_power_range[0]
        beam_power_max = beam_power_range[1]

    if len(scan_velocity_range) == 1:
        scan_velocity_min = 0
        scan_velocity_max = scan_velocity_range[0]
    else:
        scan_velocity_min = scan_velocity_range[0]
        scan_velocity_max = scan_velocity_range[1]

    if name is None:
        name = (
            f"{beam_power_min}_"
            f"{beam_power_max}_"
            f"{beam_power_units}_"
            f"{scan_velocity_min}_"
            f"{scan_velocity_max}_"
            f"{scan_velocity_units}"
        )

    # workspace = Workspace.load(workspace_path / "workspace.json")
    # if "process_maps" not in workspace.subfolders:
    #     workspace.add_subfolder("process_maps")

    process_map_out_path = workspace_path / "process_maps" / name
    process_map_out_path.mkdir(exist_ok=True, parents=True)

    build_parameters.save(process_map_out_path / "build_parameters.json")
    material.save(process_map_out_path / "material.json")

    beam_powers = range(*beam_power_range)
    scan_velocities = range(*scan_velocity_range)

    points = []
    for beam_power in beam_powers:
        for scan_velocity in scan_velocities:
            point = [
                Quantity(beam_power, beam_power_units),
                Quantity(scan_velocity, scan_velocity_units),
            ]
            points.append(point)

    process_map = ProcessMap(parameters=["beam_power", "scan_velocity"], points=points)
    process_map.save(process_map_out_path / "config.json")

    return process_map_out_path
