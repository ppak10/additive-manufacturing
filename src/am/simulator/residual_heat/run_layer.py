from datetime import datetime
from pathlib import Path
from pint import Quantity
from typing import cast
from tqdm import tqdm

from am.config import BuildParameters, Material, MeshParameters

from am.simulator.models import SolverLayer
from am.solver.mesh import SolverMesh
from am.solver.model import EagarTsai, Rosenthal
from am.simulator.models import SolverSegment


def run_layer(
    solver_layer: SolverLayer,
    build_parameters: BuildParameters,
    material: Material,
    mesh_parameters: MeshParameters,
    workspace_path: Path,
    solver: str = "eagar-tsai",
    run_name: str | None = None,
) -> Path:
    """
    2D layer solver, segments must be for a single layer.
    """

    if run_name is None:
        run_name = datetime.now().strftime("residual_heat_%Y%m%d_%H%M%S")

    mesh_out_path = workspace_path / "meshes" / run_name
    mesh_out_path.mkdir(exist_ok=True, parents=True)

    measure_out_path = workspace_path / "measurements" / run_name
    measure_out_path.mkdir(exist_ok=True, parents=True)

    initial_temperature: float = cast(
        Quantity, build_parameters.temperature_preheat
    ).magnitude

    solver_mesh = SolverMesh()
    _ = solver_mesh.initialize_grid(mesh_parameters, initial_temperature)

    zfill = len(f"{len(segments)}")

    match solver:
        case "eagar-tsai":
            model = EagarTsai(build_parameters, material, solver_mesh)
        case "rosenthal":
            model = Rosenthal(build_parameters, material, solver_mesh)
        case _:
            raise Exception("Invalid `model_name`")

    # Save solver configs
    build_parameters.save(mesh_out_path / "configs" / "build_parameters.json")
    material.save(mesh_out_path / "configs" / "material.json")
    mesh_parameters.save(mesh_out_path / "configs" / "mesh_parameters.json")

    # for segment_index, segment in tqdm(enumerate(segments[0:3])):
    for segment_index, segment in tqdm(enumerate(segments), total=len(segments)):

        # solver_mesh = self._forward(model, solver_mesh, segment)
        grid_offset: float = (
            cast(Quantity, build_parameters.temperature_preheat).to("K").magnitude
        )

        theta = model(segment)

        # TODO: Implement alternative saving functionalities that don't
        # write to disk as often.
        # Or maybe make this asynchronous.

        segment_index_string = f"{segment_index}".zfill(zfill)
        # solver_measure.grid = theta
        # solver_measure.approximate_melt_pool_dimensions(segment)
        # solver_measure.save(
        #     measure_out_path / "timesteps" / f"{segment_index_string}.pt"
        # )

        solver_mesh.diffuse(
            delta_time=segment.distance / build_parameters.scan_velocity,
            diffusivity=material.thermal_diffusivity,
            grid_offset=grid_offset,
        )

        # print(f"theta.unique: {theta.unique()}")

        solver_mesh.update_xy(segment)
        solver_mesh.graft(theta, grid_offset)

        _ = solver_mesh.save(mesh_out_path / "timesteps" / f"{segment_index_string}.pt")

    return mesh_out_path
