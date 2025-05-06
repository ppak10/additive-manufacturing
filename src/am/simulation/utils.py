import os
import pickle

from datetime import datetime

from am.segmenter import Segmenter
from am.solver import Solver 

class SimulationUtils:
    """
    Class for handling solver utility functions
    """

    def set_name(self, name=None, filename=None, segmenter=None, solver=None):
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
            if isinstance(segmenter, type):
                segmenter_name = segmenter.filename
            if isinstance(solver, type):
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

    def load_segmenter(self, segmenter: str | Segmenter):
        if isinstance(segmenter, Segmenter):
            return segmenter
        elif isinstance(segmenter, str):
            # Load segmenter if segmenter is a `segmenter.filename` value.
            segmenter_path = os.path.join("segmenters", segmenter, "segmenter.pkl")
            with open(segmenter_path, "rb") as f:
                instance = pickle.load(f)
            return instance
        else:
            return None

    def load_solver(self, solver: str | Solver):
        if isinstance(solver, Solver):
            return solver
        elif isinstance(solver, str):
            # Load solver if solver is a `solver.filename` value.
            solver_path = os.path.join("solvers", solver, "solver.pkl")
            with open(solver_path, "rb") as f:
                instance = pickle.load(f)
            return instance
        else:
            return None

