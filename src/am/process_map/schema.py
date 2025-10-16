import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, model_serializer
from pint import Quantity
from typing import Any, TypeVar

from typing_extensions import cast, ClassVar, TypedDict

from pintdantic import QuantityDict

T = TypeVar("T", bound="ProcessMap")


class ProcessMapDict(TypedDict):
    """
    Dictionary output of process map class.
    """

    parameters: list[str]
    points: list[dict[str, QuantityDict]]


class ProcessMap(BaseModel):
    """
    Overrides for Build Parameter configs.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    parameters: list[str] = []
    points: list[list[Quantity]] = []

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return cast(Quantity, Quantity(d["magnitude"], d["units"]))

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        data = handler(self)

        data["parameters"] = self.parameters
        data["points"] = []

        # Creates an dict for each point with the parameter values.
        for point in self.points:
            point_parameters = {}

            # Converts each parameter from Quantity class to dict.
            for index, parameter in enumerate(self.parameters):
                point_parameters[parameter] = self._quantity_to_dict(point[index])
            data["points"].append(point_parameters)

        return data

    @classmethod
    def load(cls: type[T], path: Path) -> T:
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(f"Unexpected JSON structure in {path}: expected dict")

    def save(self, path: Path) -> Path:
        data = self.model_dump()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        # Convert serialized points back to Quantity objects
        points = []
        if "points" in data and "parameters" in data:
            for point_dict in data["points"]:
                point = []
                for param in data["parameters"]:
                    if param in point_dict:
                        point.append(cls._dict_to_quantity(point_dict[param]))
                points.append(point)

        return cls(parameters=data.get("parameters", []), points=points)
