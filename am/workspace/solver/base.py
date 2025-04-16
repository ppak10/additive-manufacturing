from am.solver import Solver

class WorkspaceSolverBase:
    def create_solver(self, **kwargs):
        solver = Solver(**kwargs)
        self.create_solver_folder(solver)
