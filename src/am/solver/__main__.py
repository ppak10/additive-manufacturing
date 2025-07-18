import os

from pathlib import Path
from pint import UnitRegistry
from rich import print as rprint
from typing import Literal

from .config import SolverConfig


class Solver:
    """
    Base solver methods.
    """

    def __init__(
            self,
            ureg_default_system: Literal['cgs', 'mks'] = "cgs",
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

    def create_solver(self, solver_path: Path):
        # Create `solver` folder
        solver_path.mkdir(exist_ok=True)
        self.config.solver_path = solver_path
        solver_config_file = self.config.save()
        rprint(f"Solver config file saved at: {solver_config_file}")

        # Create `solver/mesh_configs` directory
        solver_meshes_path = self.config.solver_path / "mesh_configs"
        os.makedirs(solver_meshes_path, exist_ok=True)

        # Create `solver/material_configs` directory
        solver_materials_path = self.config.solver_path / "material_configs"
        os.makedirs(solver_materials_path, exist_ok=True)

        # Create `solver/models` directory
        solver_models_path = self.config.solver_path / "models"
        os.makedirs(solver_models_path, exist_ok=True)
 
        # Create `solver/simulations` directory
        solver_simulations_path = self.config.solver_path / "simulations"
        os.makedirs(solver_simulations_path, exist_ok=True)

