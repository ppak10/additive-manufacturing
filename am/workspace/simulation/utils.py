import os
import pickle

class WorkspaceSimulationUtils:
    """
    Utility functions for workspace simulation class.
    """
    def create_simulation_folder(self, simulation):
        """
        Creates folder for `simulation` and parent `simulations` folder if needed.
        Also saves passed simulation into `simulation.pkl` within created folder.
        """
        # Creates `simulations` folder path within workspace if not created.
        simulations_path = os.path.join(self.workspace_path, "simulations")
        if not os.path.isdir(simulations_path):
            os.makedirs(simulations_path)

        # Create `simulation` folder within workspace path 
        simulation_path = os.path.join(self.workspace_path, "simulations", simulation.filename)
        if not os.path.isdir(simulation_path):
            os.makedirs(simulation_path)

        # Save simulation class object to pickle file
        simulation_pkl_path = os.path.join(simulation_path, "simulation.pkl")
        with open(simulation_pkl_path, "wb") as file:
            pickle.dump(simulation, file)
        
        return simulation_path