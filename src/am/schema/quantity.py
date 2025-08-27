import json

from pint import Quantity
from pathlib import Path
from pydantic import BaseModel, ConfigDict, field_validator, model_serializer

from typing import Any
from typing_extensions import cast, ClassVar, TypedDict, TypeVar

T = TypeVar("T", bound="QuantityModel")

class QuantityDict(TypedDict):
    """
    TypedDict for Quantity serialized as dict
    """

    magnitude: float
    units: str

class QuantityModel(BaseModel):
    """
    Base pydantic model for handling parsing and serializing quantities in
    child classes.
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)
    
    _quantity_fields: ClassVar[set[str]] = set()

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
        for name in self._quantity_fields:
            value = getattr(self, name)
            if isinstance(value, Quantity):
                data[name] = self._quantity_to_dict(value)
        return data

    @field_validator("*", mode="before")
    def parse_quantity(cls, v: Any, info) -> Any:
        if info.field_name in cls._quantity_fields:
            if isinstance(v, dict):
                expected_keys = {"magnitude", "units"}
                if set(v.keys()) != expected_keys:
                    raise ValueError(f"Invalid keys for QuantityDict: {v.keys()}")
                if not isinstance(v["magnitude"], (float, int)):
                    raise ValueError(
                        f"QuantityDict magnitude must be float or int, got {type(v['magnitude'])}"
                    )
                if not isinstance(v["units"], str):
                    raise ValueError(f"QuantityDict units must be str, got {type(v['units'])}")
                return cls._dict_to_quantity(cast(QuantityDict, v))
            elif isinstance(v, Quantity):
                return v
            else:
                raise ValueError(f"Expected QuantityDict or Quantity, got {type(v)}")
        return v

    def to_dict(self) -> dict[str, Any]:
        # return self.model_dump(mode="json")
        return self.serialize_model(lambda m: m.model_dump(mode="python"))

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        return cls(**data)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.serialize_model(lambda m: m.model_dump(mode="python"))
        _ = path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def load(cls: type[T], path: Path) -> T:
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(f"Unexpected JSON structure in {path}: expected dict or list of dicts")

