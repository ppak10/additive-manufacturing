from .base import SimulationBase

class Simulation(SimulationBase):
    """
    Coordinates segmenter and solver classes.
    """
    def __init__(self, name = None, filename = None, verbose = False, **kwargs):
        """
        @param name: Specific name of simulation 
        @param filename: Filepath friendly name
        @param verbose: For debugging
        """
        super().__init__(name=name, filename=filename, verbose=verbose, **kwargs)
