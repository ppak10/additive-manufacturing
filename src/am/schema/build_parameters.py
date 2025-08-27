from pint import Quantity

from typing_extensions import cast, TypedDict

from .quantity import QuantityDict, QuantityModel, QuantityField

DEFAULT = {
    "beam_diameter": (5e-5, "meter"),
    "beam_power": (200, "watts"),
    "scan_velocity": (0.8, "meter / second"),
    "temperature_preheat": (300, "kelvin"),
}


class BuildParametersDict(TypedDict):
    beam_diameter: QuantityDict
    beam_power: QuantityDict
    scan_velocity: QuantityDict
    temperature_preheat: QuantityDict


class BuildParameters(QuantityModel):
    """
    Build configurations utilized for solver and process map.
    """

    beam_diameter: QuantityField = cast(Quantity, Quantity(*DEFAULT["beam_diameter"]))
    beam_power: QuantityField = cast(Quantity, Quantity(*DEFAULT["beam_power"]))
    scan_velocity: QuantityField = cast(Quantity, Quantity(*DEFAULT["scan_velocity"]))
    temperature_preheat: QuantityField = cast(
        Quantity, Quantity(*DEFAULT["temperature_preheat"])
    )

    _quantity_defaults = DEFAULT
    _quantity_fields = set(DEFAULT.keys())
