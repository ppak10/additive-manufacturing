import json

from pathlib import Path
from pint import Quantity
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
    field_serializer,
    ValidationError,
)
from pintdantic import QuantityDict
from typing_extensions import cast, ClassVar, TypedDict

######################
# MeltPoolDimensions #
######################


class MeltPoolDimensionsDict(TypedDict):
    depth: QuantityDict
    width: QuantityDict
    length: QuantityDict
    length_front: QuantityDict
    length_behind: QuantityDict


class MeltPoolDimensions(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    depth: Quantity
    width: Quantity
    length: Quantity
    length_front: Quantity
    length_behind: Quantity

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @field_serializer(
        "depth",
        "width",
        "length",
        "length_front",
        "length_behind",
    )
    def serialize_quantity(self, value: Quantity) -> QuantityDict:
        if isinstance(value, Quantity):
            return self._quantity_to_dict(value)
        return QuantityDict(
            magnitude=0.0,
            units="unknown",
        )

    def to_dict(self) -> MeltPoolDimensionsDict:
        return {
            "depth": self._quantity_to_dict(self.depth),
            "width": self._quantity_to_dict(self.width),
            "length": self._quantity_to_dict(self.length),
            "length_front": self._quantity_to_dict(self.length_front),
            "length_behind": self._quantity_to_dict(self.length_behind),
        }

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return Quantity(d["magnitude"], d["units"])

    @field_validator(
        "depth",
        "width",
        "length",
        "length_front",
        "length_behind",
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

    @classmethod
    def from_dict(cls, data: MeltPoolDimensionsDict) -> "MeltPoolDimensions":
        return cls(**data)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "MeltPoolDimensions":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        else:
            raise ValueError(
                f"Unexpected JSON structure in {path}: expected dict or list of dicts"
            )
