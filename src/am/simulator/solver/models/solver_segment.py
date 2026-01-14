from pintdantic import QuantityDict, QuantityModel, QuantityField
from typing_extensions import TypedDict

# TODO: If 3D (z axis) is ever needed for some reason make new SolverSegment3D.
# 2025-12-18 I don't think that will happen as the applications of this are
# going to be planar. Though if there's something were 3D simulation is needed
# say for non-planar FDM print, making a new model would probably be better for
# that specific case.


class SolverSegmentDict(TypedDict):
    x1: QuantityDict
    y1: QuantityDict
    x2: QuantityDict
    y2: QuantityDict
    angle: QuantityDict
    distance: QuantityDict
    travel: bool


class SolverSegment(QuantityModel):
    """
    Segments for providing tool path instructions to solver.
    """

    x1: QuantityField
    y1: QuantityField
    x2: QuantityField
    y2: QuantityField
    angle: QuantityField
    distance: QuantityField
    travel: bool
