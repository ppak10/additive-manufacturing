from am.solver import Solver


class WorkspaceSolverBase:
    def solver_initialize(self, **kwargs):
        solver = Solver(**kwargs)
        self.create_solver_folder(solver, save=True)

    # Aliases
    solver_init = solver_initialize
