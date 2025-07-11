from .base import SimulationBase
from .utils import SimulationUtils
from .visualize import SimulationVisualize


class Simulation(SimulationBase, SimulationUtils, SimulationVisualize):
    """
    Coordinates segmenter and solver classes.
    """

    def __init__(
        self,
        segmenter=None,
        solver=None,
        name=None,
        filename=None,
        zfill=8,
        verbose=False,
        **kwargs,
    ):
        """
        @param segmenter: Segmenter class instantiation or filename
        @param solver: Solver class instantiation or filename
        @param name: Specific name of simulation
        @param filename: Filepath friendly name
        @param zfill: .zfill() value used for preceding zeros.
        @param verbose: For debugging
        """
        super().__init__(
            segmenter=segmenter,
            solver=solver,
            name=name,
            filename=filename,
            zfill=zfill,
            verbose=verbose,
            **kwargs,
        )
