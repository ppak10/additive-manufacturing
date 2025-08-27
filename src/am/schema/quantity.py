import json

from pint import Quantity
from pathlib import Path
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
    model_validator,
    model_serializer,
)

from typing import Any, Tuple, Union
from typing_extensions import cast, ClassVar, TypedDict, TypeVar

T = TypeVar("T", bound="QuantityModel")

QuantityInput = Union[float, int, Tuple[float | int, str]]

QuantityField = Quantity | QuantityInput | None


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

    _quantity_defaults: ClassVar[dict[str, Tuple[float | int, str]]] = {}
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

    @model_validator(mode="before")
    def coerce_quantity_inputs(cls, values: dict[str, Any]) -> dict[str, Any]:
        for field in cls._quantity_defaults:
            val = values.get(field)
            if isinstance(val, (float, int)):
                # Use default units
                mag, unit = cls._quantity_defaults[field]
                values[field] = Quantity(val, unit)
            elif isinstance(val, tuple) and len(val) == 2:
                # Tuple (magnitude, unit)
                values[field] = Quantity(*val)
            elif isinstance(val, dict) and "magnitude" in val and "units" in val:
                # Dict input
                values[field] = Quantity(val["magnitude"], val["units"])
            # If already a Quantity, do nothing
        return values

    @field_validator("*", mode="before")
    def parse_quantity(cls, v: Any, info) -> Any:
        if info.field_name in cls._quantity_fields:
            if isinstance(v, Quantity):
                return v

            elif isinstance(v, dict):
                expected_keys = {"magnitude", "units"}
                if set(v.keys()) != expected_keys:
                    raise ValueError(f"Invalid keys for QuantityDict: {v.keys()}")
                if not isinstance(v["magnitude"], (float, int)):
                    raise ValueError(
                        f"QuantityDict magnitude must be float or int, got {type(v['magnitude'])}"
                    )
                if not isinstance(v["units"], str):
                    raise ValueError(
                        f"QuantityDict units must be str, got {type(v['units'])}"
                    )
                return cls._dict_to_quantity(cast(QuantityDict, v))

            elif isinstance(v, Tuple):
                if len(v) != 2:
                    raise ValueError(
                        f"Expected exact length of 2 (magnitude, units) if tuple is provided"
                    )
                if not isinstance(v[0], (float, int)):
                    raise ValueError(
                        f"Magnitude must be float or int, got {type(v[0])}"
                    )
                if not isinstance(v[1], str):
                    raise ValueError(f"Units must be str, got {type(v[1])}")

                return Quantity(v[0], v[1])

            elif isinstance(v, (float, int)):
                if info.field_name not in cls._quantity_defaults:
                    raise ValueError(f"Units not provided in _quantity_defaults")
                units = cls._quantity_defaults[info.field_name][1]
                return Quantity(v, units)

            else:
                raise ValueError(
                    f"Expected Float, Int, Tuple, QuantityDict, Quantity, got {type(v)}"
                )
        return v

    @classmethod
    def load(cls: type[T], path: Path) -> T:
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(
            f"Unexpected JSON structure in {path}: expected dict or list of dicts"
        )

    def save(self, path):
        data = self.to_dict()  # Convert all Quantities to dicts first
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        # Ensure quantity fields are parsed from dicts if needed
        for name in cls._quantity_fields:
            if name in data and isinstance(data[name], dict):
                data[name] = cls._dict_to_quantity(data[name])
        return cls(**data)

    def to_dict(self):
        out = {}

        for field, value in self.__dict__.items():
            if field in self._quantity_fields:
                if isinstance(value, Quantity):
                    out[field] = {
                        "magnitude": value.magnitude,
                        "units": str(value.units),
                    }
                elif isinstance(value, (tuple, list)) and len(value) == 2:
                    mag, unit = value
                    out[field] = {"magnitude": mag, "units": unit}
                elif isinstance(value, (float, int)):
                    # Only use defaults if they exist
                    if (
                        hasattr(self, "_quantity_defaults")
                        and field in self._quantity_defaults
                    ):
                        _, unit = self._quantity_defaults[field]
                        out[field] = {"magnitude": value, "units": unit}
            else:
                out[field] = value
        return out
