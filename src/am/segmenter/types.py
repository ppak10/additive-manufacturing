import json

from pydantic import BaseModel, ConfigDict, field_validator, ValidationError
from pint import Quantity
from pathlib import Path
from typing import Any, ClassVar, TypedDict


class Command(TypedDict):
    x: Quantity
    y: Quantity
    z: Quantity
    e: Quantity


# TypedDict for Quantity serialized as dict
class QuantityDict(TypedDict):
    magnitude: float
    units: str


# SegmentDict with QuantityDict for quantities and bool for travel
class SegmentDict(TypedDict):
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


class Segment(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)
    x: Quantity
    y: Quantity
    z: Quantity
    e: Quantity
    x_next: Quantity
    y_next: Quantity
    z_next: Quantity
    e_next: Quantity
    angle_xy: Quantity
    distance_xy: Quantity
    travel: bool

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": q.magnitude, "units": str(q.units)}

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return Quantity(d["magnitude"], d["units"])

    @field_validator(
        "x",
        "y",
        "z",
        "e",
        "x_next",
        "y_next",
        "z_next",
        "e_next",
        "angle_xy",
        "distance_xy",
        mode="before",
    )
    def parse_quantity(cls, v: QuantityDict | Quantity) -> Quantity:
        if isinstance(v, dict):
            # Strict check keys and types
            expected_keys = {"magnitude", "units"}
            if set(v.keys()) != expected_keys:
                raise ValidationError(
                    f"Invalid keys for QuantityDict, expected {expected_keys} but got {v.keys()}"
                )
            if not isinstance(v["magnitude"], float):
                raise ValidationError(
                    f"QuantityDict magnitude must be float, got {type(v['magnitude'])}"
                )
            if not isinstance(v["units"], str):
                raise ValidationError(
                    f"QuantityDict units must be str, got {type(v['units'])}"
                )
            return cls._dict_to_quantity(v)
        elif isinstance(v, Quantity):
            return v
        else:
            raise ValidationError(f"Expected QuantityDict or Quantity, got {type(v)}")

    def to_dict(self) -> SegmentDict:
        return {
            "x": self._quantity_to_dict(self.x),
            "y": self._quantity_to_dict(self.y),
            "z": self._quantity_to_dict(self.z),
            "e": self._quantity_to_dict(self.e),
            "x_next": self._quantity_to_dict(self.x_next),
            "y_next": self._quantity_to_dict(self.y_next),
            "z_next": self._quantity_to_dict(self.z_next),
            "e_next": self._quantity_to_dict(self.e_next),
            "angle_xy": self._quantity_to_dict(self.angle_xy),
            "distance_xy": self._quantity_to_dict(self.distance_xy),
            "travel": self.travel,
        }

    @classmethod
    def from_dict(cls, data: SegmentDict) -> "Segment":
        return cls(**data)

    @classmethod
    def load(cls, path: Path) -> list["Segment"]:
        with path.open("r") as f:
            data = json.load(f)

        if isinstance(data, list):
            return [cls.from_dict(item) for item in data]
        elif isinstance(data, dict):
            return [cls.from_dict(data)]
        else:
            raise ValueError(
                f"Unexpected JSON structure in {path}: expected dict or list of dicts"
            )
