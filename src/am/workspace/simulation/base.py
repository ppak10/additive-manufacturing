import os
import pickle

from am.simulation import Simulation

class WorkspaceSimulationBase:
    def create_simulation(self, **kwargs):
        """
        Main entrypoint for creating a simulation configuration that combines
        build, material, and mesh parameters.
        """
        simulation = Simulation(**kwargs)
        self.create_simulation_folders(simulation, save_simulation=True)

    def run_simulation_layer(self, layer_index: int, **kwargs):
        """
        Creates and runs simulation for a specified layer index.

        `create_simulation` should have been run beforehand.

        Args:
            layer_index (int): Layer index to run simulation for.
            **simulation_folder_name (Optional[str]): Name of the simulation
                folder where `simulation.pkl` can be found.
            **solver_folder_name (Optional[str]): Name of the already created
                solver to use when running the simulation.
            **segmenter_folder_name (Optional[str]): Name of the already created
                segmenter that provides path data for the simulation.
        """

        # TODO: Move to decorator
        # Prompts user to select simulation folder if simulation folder name is
        # not provided.
        simulation_folder = kwargs.get("simulation_folder_name")
        if not simulation_folder:
            simulation_folder = self.select_folder("simulations")

        solver_folder = kwargs.get("solver_folder_name")
        if not solver_folder:
            solver_folder = self.select_folder("solvers")

        segmenter_folder = kwargs.get("segmenter_folder_name")
        if not segmenter_folder:
            segmenter_folder = self.select_folder("segmenters")

        # Locations of saved Simulation, Solver, and Segmenter classes.
        simulation_path = os.path.join(
            "simulations", simulation_folder, "simulation.pkl"
        )
        solver_path = os.path.join("solvers", solver_folder, "solver.pkl")
        segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")

        # Load pickled objects
        with open(simulation_path, "rb") as f:
            simulation = pickle.load(f)

        with open(solver_path, "rb") as f:
            solver = pickle.load(f)

        with open(segmenter_path, "rb") as f:
            segmenter = pickle.load(f)

        # Creates initial folders if not already made.
        # Should already be made from running `create_simulation`
        self.create_simulation_folders(simulation)

        # Appends zeros to layer index value for file ordering purposes.
        layer_index_string = f"{layer_index}".zfill(8)
        out_dir = os.path.join(
            # i.e. `/out/test/simulations/test_simulation/layers/00000001/timesteps`
            "simulations",
            simulation_folder,
            "layers",
            layer_index_string,
            "timesteps",
        )
        simulation.run_layer_index(segmenter, solver, layer_index, out_dir)

    def visualize_simulation_layer(self, layer_index: int, **kwargs):
        # TODO: Move to decorator
        # Prompts user to select simulation folder if simulation folder name is
        # not provided.
        simulation_folder = kwargs.get("simulation_folder_name")
        if not simulation_folder:
            simulation_folder = self.select_folder("simulations")

        solver_folder = kwargs.get("solver_folder_name")
        if not solver_folder:
            solver_folder = self.select_folder("solvers")

        segmenter_folder = kwargs.get("segmenter_folder_name")
        if not segmenter_folder:
            segmenter_folder = self.select_folder("segmenters")

        # Locations of saved Simulation, Solver, and Segmenter classes.
        simulation_path = os.path.join(
            "simulations", simulation_folder, "simulation.pkl"
        )
        solver_path = os.path.join("solvers", solver_folder, "solver.pkl")
        segmenter_path = os.path.join("segmenters", segmenter_folder, "segmenter.pkl")

        # Load pickled objects
        with open(simulation_path, "rb") as f:
            simulation = pickle.load(f)

        with open(solver_path, "rb") as f:
            solver = pickle.load(f)

        with open(segmenter_path, "rb") as f:
            segmenter = pickle.load(f)

