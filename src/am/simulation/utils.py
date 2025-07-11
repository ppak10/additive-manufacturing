import os
import pickle

from datetime import datetime

from am.segmenter import Segmenter
from am.solver import Solver


class SimulationUtils:
    """
    Class for handling solver utility functions
    """

    def set_name(
        self,
        name=None,
        filename=None,
        segmenter=None,
        segmenter_path=None,
        solver=None,
        solver_path=None,
    ):
        """
        Sets the `name` and `filename` values of the class.

        @param name: Name of simulation
        @param filename: `filename` override of simulation (no spaces)
        """
        if name:
            self.name = name
        elif segmenter is not None and solver is not None:
            segmenter_name = segmenter
            solver_name = solver

            # Handles case if class is passed in
            if isinstance(segmenter, Segmenter):
                segmenter_name = segmenter.filename
            if isinstance(solver, Solver):
                solver_name = solver.filename

            self.name = f"{segmenter_name}_{solver_name}"
        elif segmenter_path is not None and solver_path is not None:
            segmenter_name = os.path.basename(os.path.dirname(segmenter_path))
            solver_name = os.path.basename(os.path.dirname(solver_path))

            # Handles case if class is passed in
            if isinstance(segmenter, Segmenter):
                segmenter_name = segmenter.filename
            if isinstance(solver, Solver):
                solver_name = solver.filename

            self.name = f"{segmenter_name}_{solver_name}"
        else:
            # Sets `name` to approximate timestamp.
            self.name = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Autogenerates `filename` from `name` if not provided.
        if filename == None:
            self.filename = self.name.replace(" ", "_")
        else:
            self.filename = filename

    def load_segmenter(self, segmenter: str | Segmenter = None):
        if isinstance(segmenter, Segmenter):
            self.segmenter = segmenter
        elif isinstance(segmenter, str):
            # Load segmenter if segmenter is a `segmenter.filename` value.
            segmenter_path = os.path.join("segmenters", segmenter, "segmenter.pkl")
            with open(segmenter_path, "rb") as f:
                self.segmenter = pickle.load(f)
        elif self.segmenter_path is not None:
            with open(self.segmenter_path, "rb") as f:
                self.segmenter = pickle.load(f)
        else:
            self.segmenter = None

    def load_solver(self, solver: str | Solver = None):
        if isinstance(solver, Solver):
            self.solver = solver
        elif isinstance(solver, str):
            # Load solver if solver is a `solver.filename` value.
            solver_path = os.path.join("solvers", solver, "solver.pkl")
            with open(solver_path, "rb") as f:
                self.solver = pickle.load(f)
        elif self.solver_path is not None:
            with open(self.solver_path, "rb") as f:
                self.solver = pickle.load(f)
        else:
            self.solver = None
