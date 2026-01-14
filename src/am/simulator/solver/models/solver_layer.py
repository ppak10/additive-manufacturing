from pathlib import Path
from pydantic import BaseModel
from typing import Union

from .solver_segment import SolverSegment

# TODO: If 3D (z axis) is ever needed for some reason make new SolverSegment3D.
# 2025-12-18 I don't think that will happen as the applications of this are
# going to be planar. Though if there's something were 3D simulation is needed
# say for non-planar FDM print, making a new model would probably be better for
# that specific case.


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
