from typing_extensions import TypedDict

from pintdantic import QuantityDict, QuantityModel, QuantityField


class SolverSegmentDict(TypedDict):
    x: QuantityDict
    y: QuantityDict
    z: QuantityDict
    e: QuantityDict
    x_next: QuantityDict
    y_next: QuantityDict
    z_next: QuantityDict
    e_next: QuantityDict
    angle_xy: QuantityDict
    distance_xy: QuantityDict
    travel: bool


class SolverSegment(QuantityModel):
    """
    Segments for providing tool path instructions to solver.
    """

    x: QuantityField
    y: QuantityField
    z: QuantityField
    e: QuantityField
    x_next: QuantityField
    y_next: QuantityField
    z_next: QuantityField
    e_next: QuantityField
    angle_xy: QuantityField
    distance_xy: QuantityField
    travel: bool
