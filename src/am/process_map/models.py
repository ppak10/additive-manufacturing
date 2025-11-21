import json

from pathlib import Path
from pydantic import BaseModel

from am.config import BuildParameters
from am.solver.types import MeltPoolDimensions


class MeltPoolClassifications(BaseModel):
    lack_of_fusion: bool | None = None
    keyholing: bool | None = None
    balling: bool | None = None


class ProcessMapPoint(BaseModel):
    """
    Extends Build Parameters for process map point.
    """

    build_parameters: BuildParameters
    melt_pool_dimensions: MeltPoolDimensions
    melt_pool_classifications: MeltPoolClassifications

    def to_dict(self) -> dict:
        """Convert ProcessMapPoint to dictionary with proper serialization."""
        return {
            "build_parameters": self.build_parameters.to_dict(),
            "melt_pool_dimensions": self.melt_pool_dimensions.to_dict(),
            "melt_pool_classifications": self.melt_pool_classifications.model_dump(),
        }

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        _ = path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "ProcessMapPoint":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls(**data)
        else:
            raise ValueError(f"Unexpected JSON structure in {path}: expected dict")


# TODO: Rename this ProcessMap as to include more fields
class ProcessMapPoints(BaseModel):
    """
    Collection of ProcessMapPoint values.
    """

    points: list[ProcessMapPoint] = []

    def to_dict(self) -> dict:
        """Convert ProcessMapPoints to dictionary with proper serialization."""
        return {"points": [point.to_dict() for point in self.points]}

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.to_dict()
        _ = path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "ProcessMapPoints":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls(**data)
        else:
            raise ValueError(f"Unexpected JSON structure in {path}: expected dict")
