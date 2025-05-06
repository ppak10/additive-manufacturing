from .base import SegmenterBase
from .gcode import SegmenterGCode
from .visualize import SegmenterVisualize

from am.units import MMGS


class Segmenter(SegmenterBase, SegmenterGCode, SegmenterVisualize):
    def __init__(self, name=None, filename=None, units=MMGS, zfill=8, verbose=False, **kwargs):
        """
        @param name: Specific name of segmenter
        @param filename: Filepath friendly name
        @param units: Defaults to mmgs (Millimeter Gram Second Degree)
        @param zfill: .zfill amount used will generating preceding zeros.
        @param verbose: For debugging
        """
        super().__init__(
            name=name, filename=filename, units=units, zfill=zfill, verbose=verbose, **kwargs
        )
