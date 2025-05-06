import os
import pickle


class WorkspaceSimulationUtils:
    """
    Utility functions for workspace simulation class.
    """

    def create_simulation_folders(self, simulation, save=False):
        """
        Creates file and folders for `simulation`.
        Also creates parent `simulations` folder if not existant.
        """

        # Should happen just once for each workspace initialization.
        simulations_path = os.path.join(
            # `/out/<self.workspace_path>/simulations/`
            self.workspace_path,
            "simulations",
        )
        if not os.path.isdir(simulations_path):
            os.makedirs(simulations_path)

        # Creates folder for housing simulation layers and visualizations.
        simulation_path = os.path.join(
            # `/out/<self.workspace_path>/simulations/<simulation.filename>/`
            self.workspace_path,
            "simulations",
            simulation.filename,
        )
        if not os.path.isdir(simulation_path):
            os.makedirs(simulation_path)

        # Creates folder for simulation layers.
        simulation_layers_path = os.path.join(
            # `/out/<self.workspace_path>/simulations/<simulation.filename>/layers/`
            self.workspace_path,
            "simulations",
            simulation.filename,
            "layers",
        )

        if not os.path.isdir(simulation_layers_path):
            os.makedirs(simulation_layers_path)

        if save:
            # Creates simulation pickle file.
            simulation_pkl_path = os.path.join(
                # `/out/<self.workspace_path>/simulations/<simulation.filename>/simulation.pkl`
                simulation_path,
                "simulation.pkl",
            )
            with open(simulation_pkl_path, "wb") as file:
                pickle.dump(simulation, file)

        return simulation_path
