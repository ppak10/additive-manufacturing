import imageio.v2 as imageio
import matplotlib.pyplot as plt

from datetime import datetime
from io import BytesIO
from pathlib import Path
from pint import UnitRegistry
from rich import print as rprint
from typing import cast, Literal
from tqdm import tqdm

from .config import SolverConfig

from am.segmenter.types import Segment
from am.solver.types import BuildConfig, MaterialConfig, MeshConfig
from am.solver.mesh import SolverMesh
from am.solver.model import EagarTsai, Rosenthal


class Solver:
    """
    Base solver methods.
    """

    def __init__(
        self,
        ureg_default_system: Literal["cgs", "mks"] = "cgs",
        ureg: UnitRegistry | None = None,
        solver_path: Path | None = None,
        verbose: bool | None = False,
    ):
        self.config: SolverConfig = SolverConfig(
            ureg_default_system=ureg_default_system,
            solver_path=solver_path,
        )

    @property
    def ureg(self):
        return self.config.ureg

    @property
    def solver_path(self):
        return self.config.solver_path

    @solver_path.setter
    def solver_path(self, value: Path):
        self.config.solver_path = value

    def create_solver_config(self, solver_path: Path):
        # Create `solver` folder
        solver_path.mkdir(exist_ok=True)
        self.config.solver_path = solver_path
        solver_config_file = self.config.save()
        rprint(f"Solver config file saved at: {solver_config_file}")

    def create_default_configs(self, config_path: Path | None = None):
        if config_path is None:
            if self.config.solver_path:
                config_path = self.config.solver_path / "config"
            else:
                config_path = Path.cwd() / "config"

        build_config = BuildConfig.create_default(self.ureg)
        build_config_path = config_path / "build" / "default.json"
        _ = build_config.save(build_config_path)

        material_config = MaterialConfig.create_default(self.ureg)
        material_config_path = config_path / "material" / "default.json"
        _ = material_config.save(material_config_path)

        mesh_config = MeshConfig.create_default(self.ureg)
        mesh_config_path = config_path / "mesh" / "default.json"
        _ = mesh_config.save(mesh_config_path)

    def run_layer(
        self,
        segments: list[Segment],
        build_config: BuildConfig,
        material_config: MaterialConfig,
        mesh_config: MeshConfig,
        model_name: str = "eagar-tsai",
        run_name: str | None = None,
    ) -> Path:
        """
        2D layer solver, segments must be for a single layer.
        """

        if run_name is None:
            run_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")

        cwd = Path.cwd()
        run_out_path = cwd / "solver" / "runs" / run_name
        run_out_path.mkdir(exist_ok=True, parents=True)

        initial_temperature = cast(float, build_config.temperature_preheat.magnitude)

        solver_mesh = SolverMesh(self.config, mesh_config)
        _ = solver_mesh.initialize_grid(initial_temperature)

        zfill = len(f"{len(segments)}")

        match model_name:
            case "eagar-tsai":
                model = EagarTsai(build_config, material_config, solver_mesh)
            case "rosenthal":
                model = Rosenthal(build_config, material_config, solver_mesh)
            case _:
                raise Exception("Invalid `model_name`")

        # for segment_index, segment in tqdm(enumerate(segments[0:3])):
        for segment_index, segment in tqdm(enumerate(segments), total=len(segments)):

            # solver_mesh = self._forward(model, solver_mesh, segment)
            grid_offset = cast(
                float, build_config.temperature_preheat.to("K").magnitude
            )

            theta = model(segment)

            solver_mesh.diffuse(
                delta_time=segment.distance_xy / build_config.scan_velocity,
                diffusivity=material_config.thermal_diffusivity,
                grid_offset=grid_offset,
            )

            # print(f"theta.unique: {theta.unique()}")

            solver_mesh.update_xy(segment)
            solver_mesh.graft(theta, grid_offset)

            # TODO: Implement alternative saving functionalities that don't
            # write to disk as often.
            # Or maybe make this asynchronous.
            segment_index_string = f"{segment_index}".zfill(zfill)
            _ = solver_mesh.save(run_out_path / "meshes" / f"{segment_index_string}.pt")

        return run_out_path

    @staticmethod
    def visualize_2D(
        run_path: Path,
        cmap: str = "plasma",
        frame_format: str = "png",
        include_axis: bool = True,
        label: str = "Temperature (K)",
        vmin: float = 300,
        vmax: float | None = 1000,
        transparent: bool = False,
        units: str = "mm",
        verbose: bool = False,
    ):
        """
        Visualizes meshes in given run folder.
        """

        visualizations_path = run_path / "visualizations"
        visualizations_path.mkdir(exist_ok=True, parents=True)

        frames_path = visualizations_path / "frames"
        frames_path.mkdir(exist_ok=True, parents=True)

        mesh_folder = run_path / "meshes"
        mesh_files = sorted([f.name for f in mesh_folder.iterdir() if f.is_file()])

        animation_out_path = visualizations_path / "frames.gif"
        writer = imageio.get_writer(animation_out_path, mode="I", duration=0.1, loop=0)

        for mesh_file in tqdm(mesh_files):
            mesh_index_string = Path(mesh_file).stem
            solver_mesh = SolverMesh.load(mesh_folder / mesh_file)
            fig_path = frames_path / f"{mesh_index_string}.png"
            fig, _, _ = solver_mesh.visualize_2D(
                cmap=cmap,
                include_axis=include_axis,
                label=label,
                vmin=vmin,
                vmax=vmax,
                transparent=transparent,
                units=units,
            )
            fig.savefig(fig_path, dpi=600, bbox_inches="tight")
            plt.close(fig)

            # Copy image to memory for later
            buffer = BytesIO()
            fig.savefig(buffer, format=frame_format, transparent=transparent)
            buffer.seek(0)
            writer.append_data(imageio.imread(buffer))

            plt.close(fig)

        writer.close()

    def run(self) -> None:
        # TODO: Save for 3D implementation
        raise NotImplementedError("Not yet implemented")
