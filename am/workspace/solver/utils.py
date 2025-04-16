import os
import pickle

class WorkspaceSolverUtils:
    """
    Utility functions for workspace solver class.
    """
    def create_solver_folder(self, solver):
        """
        Creates folder for `solver` and parent `solvers` folder if needed.
        Also saves passed solver into `solver.pkl` within created folder.
        """
        # Creates `solvers` folder path within workspace if not created.
        solvers_path = os.path.join(self.workspace_path, "solvers")
        if not os.path.isdir(solvers_path):
            os.makedirs(solvers_path)

        # Create `solver` folder within workspace path 
        solver_path = os.path.join(self.workspace_path, "solvers", solver.filename)
        if not os.path.isdir(solver_path):
            os.makedirs(solver_path)

        # Save solver class object to pickle file
        solver_pkl_path = os.path.join(solver_path, "solver.pkl")
        with open(solver_pkl_path, "wb") as file:
            pickle.dump(solver, file)
        
        return solver_path