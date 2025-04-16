import os
import pickle

from am.simulation import Simulation

class WorkspaceSimulationBase:
    def create_simulation(self, **kwargs):
        simulation = Simulation(**kwargs)
        self.create_simulation_folder(simulation)

    def run_simulation(self, layer_index, **kwargs):
        simulation_folder = self.select_folder("simulations")
        solver_folder = self.select_folder("solvers")
        segmenter_folder = self.select_folder("segmenters")

        simulation_path = os.path.join("simulations", simulation_folder, "simulation.pkl")
        solver_path = os.path.join("solvers", solver_folder, "solver.pkl")
        segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")


        # Load pickled objects
        with open(simulation_path, "rb") as f:
            simulation = pickle.load(f)

        with open(solver_path, "rb") as f:
            solver = pickle.load(f)

        with open(segmenter_path, "rb") as f:
            segmenter = pickle.load(f)

        out_dir = os.path.join("simulations", simulation_folder, "timesteps")
        simulation.run_layer_index(segmenter, solver, layer_index, out_dir)
