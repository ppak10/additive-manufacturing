from typing_extensions import TypedDict
from pathlib import Path
from typing import Union

from pydantic import BaseModel
from pintdantic import QuantityDict, QuantityModel, QuantityField

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


class SolverLayer(BaseModel):
    """
    Layer for solver
    """

    layer_index: int
    layer_count: int
    segments: list[SolverSegment]

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> "SolverLayer":
        """
        Load a SolverLayer from a JSON file.

        Args:
            file_path: Path to the JSON file containing the layer data

        Returns:
            SolverLayer instance

        Example:
            >>> layer = SolverLayer.load("layer_001.json")
        """
        path = Path(file_path)
        with path.open("r") as f:
            data = f.read()
        return cls.model_validate_json(data)

