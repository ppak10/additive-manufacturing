from .base import SegmenterBase
from .gcode import SegmenterGCode
from .visualize import SegmenterVisualize

class Segmenter(SegmenterBase, SegmenterGCode, SegmenterVisualize):
    def __init__(self, name=None, filename=None, verbose=False, **kwargs):
        """
        @param name: Specific name of segmenter
        @param filename: Filepath friendly name
        @param verbose: For debugging
        """
        super().__init__(name=name, filename=filename, verbose=verbose, **kwargs)
