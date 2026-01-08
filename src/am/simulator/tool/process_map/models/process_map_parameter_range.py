from pintdantic import QuantityDict, QuantityField, QuantityModel
from pydantic import model_validator, field_validator, computed_field
from typing_extensions import TypedDict
from typing import Any, TypeAlias

# First three are used as default
DEFAULTS = {
    "beam_power": {
        "start": (100, "watts"),
        "stop": (1000, "watts"),
        "step": (100, "watts"),
    },
    "scan_velocity": {
        "start": (100, "millimeter / second"),
        "stop": (2000, "millimeter / second"),
        "step": (100, "millimeter / second"),
    },
    "layer_height": {
        "start": (25, "microns"),
        "stop": (100, "microns"),
        "step": (25, "microns"),
    },
    "hatch_spacing": {
        "start": (25, "microns"),
        "stop": (100, "microns"),
        "step": (25, "microns"),
    },
    "beam_diameter": {
        "start": (50, "microns"),
        "stop": (100, "microns"),
        "step": (25, "microns"),
    },
    "temperature_preheat": {
        "start": (300, "kelvin"),
        "stop": (500, "kelvin"),
        "step": (100, "kelvin"),
    },
}

ProcessMapParameterRangeInputTuple: TypeAlias = tuple[
    list[str] | None,  # Input Shorthand
    str | None,  # Parameter Name
    list[int] | None,  # Range (start, stop, step)
    str | None,  # Units
]


class ProcessMapParameterRangeDict(TypedDict):
    name: str
    start: QuantityDict
    stop: QuantityDict
    step: QuantityDict


class ProcessMapParameterRange(QuantityModel):
    """
    Parameter range model indiating start, stop, step, and name of an
    investigated parameter for a process map
    (i.e. "beam_power", "scan_velocity", "layer_height").

    Only parameter names defined in DEFAULTS are valid.
    """

    name: str
    start: QuantityField
    stop: QuantityField
    step: QuantityField

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is one of the allowed parameter names."""
        if v not in DEFAULTS:
            valid_names = ", ".join(sorted(DEFAULTS.keys()))
            raise ValueError(
                f"Invalid parameter name '{v}'. Must be one of: {valid_names}"
            )
        return v

    @model_validator(mode="before")
    @classmethod
    def set_defaults_by_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            name = data.get("name")
            if name in DEFAULTS:
                # Only set defaults if the fields are not already provided
                if "start" not in data:
                    data["start"] = DEFAULTS[name]["start"]
                if "stop" not in data:
                    data["stop"] = DEFAULTS[name]["stop"]
                if "step" not in data:
                    data["step"] = DEFAULTS[name]["step"]
        return data

    @model_validator(mode="after")
    def validate_units_match(self) -> "ProcessMapParameterRange":
        """Validate that start, stop, and step all have the same units."""
        start_units = str(self.start.units)
        stop_units = str(self.stop.units)
        step_units = str(self.step.units)

        if not (start_units == stop_units == step_units):
            raise ValueError(
                f"All fields must have the same units. "
                f"Got start: {start_units}, stop: {stop_units}, step: {step_units}"
            )
        return self

    @computed_field
    @property
    def units(self) -> str:
        """Read-only units field derived from the step field."""
        return str(self.step.units)
