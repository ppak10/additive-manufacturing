import json

from pint import Quantity
from pathlib import Path
from pydantic import BaseModel, ConfigDict, model_validator, model_serializer

from typing import Any, Tuple
from typing_extensions import cast, ClassVar, TypeAlias, TypedDict, TypeVar

T = TypeVar("T", bound="QuantityModel")

Number: TypeAlias = float | int
QuantityInput = Number | Tuple[Number, str]
QuantityField = Quantity | QuantityInput | None


def parse_cli_input(
    value: str | None | tuple[Number, str] | Any
) -> QuantityInput | None:
    """
    Convert CLI input into a QuantityInput type.

    Accepted formats:
      "5"                  -> 5 (int)
      "5.5"                -> 5.5 (float)
      "5e-5"               -> 5e-5 (float)
      "5,meter"            -> (5, "meter")
      "1.1 m/s"            -> (1.1, "m/s")
      None                 -> None
      (5, "m")             -> (5, "m")   (passthrough)
      "(5e-05, 'meter')"   -> (5e-05, "meter")
    """
    if value is None:
        return None

    # If already a tuple, pass through
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(f"Invalid quantity tuple: {value!r}")
        num, unit = value
        if not isinstance(num, (int, float)) or not isinstance(unit, str):
            raise ValueError(f"Invalid types in tuple: {value!r}")
        return num, unit

    if not isinstance(value, str):
        raise TypeError(f"Unsupported type for quantity: {type(value)}")

    value = value.strip()

    # Handle stringified tuple input like "(5e-05, 'meter')"
    if value.startswith("(") and value.endswith(")"):
        try:
            parsed = eval(value, {"__builtins__": {}})
            if isinstance(parsed, tuple) and len(parsed) == 2:
                num, unit = parsed
                if isinstance(num, (int, float)) and isinstance(unit, str):
                    return num, unit
        except Exception:
            raise ValueError(f"Invalid tuple-like quantity string: {value!r}")

    try:
        # number,unit (comma separated)
        if "," in value:
            num_str, unit = value.split(",", 1)
            num_str = num_str.strip()
            unit = unit.strip().strip("'\"")
            number = (
                float(num_str)
                if "." in num_str or "e" in num_str.lower()
                else int(num_str)
            )
            return (number, unit)

        # number unit (space separated, e.g. "1.1 m/s")
        parts = value.split(maxsplit=1)
        if len(parts) == 2:
            num_str, unit = parts
            number = (
                float(num_str)
                if "." in num_str or "e" in num_str.lower()
                else int(num_str)
            )
            return (number, unit.strip())

        # plain number
        return float(value) if "." in value or "e" in value.lower() else int(value)

    except Exception as e:
        raise ValueError(f"Invalid quantity string: {value!r}") from e


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
    @classmethod
    def coerce_quantity_inputs(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Convert various input formats to Quantity objects before field validation"""
        for field in cls._quantity_fields:
            if field not in values:
                # Use default if field not provided
                if field in cls._quantity_defaults:
                    mag, unit = cls._quantity_defaults[field]
                    values[field] = Quantity(mag, unit)
                continue

            v = values[field]

            # Already a Quantity, keep as is
            if isinstance(v, Quantity):
                continue

            # Just a number - use default units
            elif isinstance(v, (float, int)):
                if field in cls._quantity_defaults:
                    _, unit = cls._quantity_defaults[field]
                    values[field] = Quantity(v, unit)
                else:
                    raise ValueError(f"No default units for field {field}")

            # Tuple (magnitude, unit)
            elif isinstance(v, tuple) and len(v) == 2:
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
                values[field] = Quantity(v[0], v[1])

            # Dict input
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
                values[field] = Quantity(v["magnitude"], v["units"])

            # Invalid type
            else:
                raise ValueError(f"Invalid input for quantity field {field}: {type(v)}")

        return values

    @classmethod
    def load(cls: type[T], path: Path) -> T:
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        raise ValueError(f"Unexpected JSON structure in {path}: expected dict")

    def save(self, path):
        data = self.to_dict()  # Convert all Quantities to dicts first
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))
        return path

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        # Data will be processed by model_validator automatically
        return cls(**data)

    def to_dict(self):
        out = {}
        for field in self.__class__.model_fields:
            if field in self._quantity_fields:
                value = getattr(self, field)
                if isinstance(value, Quantity):
                    out[field] = {
                        "magnitude": value.magnitude,
                        "units": str(value.units),
                    }
                else:
                    # This shouldn't happen if validators work correctly
                    out[field] = value
            else:
                value = getattr(self, field)
                out[field] = value
        return out
