from typing_extensions import TypedDict

from .quantity import QuantityDict, QuantityModel, QuantityField

DEFAULT = {
    "beam_diameter": (5e-5, "meter"),
    "beam_power": (200, "watts"),
    "hatch_spacing": (50, "microns"),
    "layer_height": (100, "microns"),
    "scan_velocity": (0.8, "meter / second"),
    "temperature_preheat": (300, "kelvin"),
}


class BuildParametersDict(TypedDict):
    beam_diameter: QuantityDict
    beam_power: QuantityDict
    hatch_spacing: QuantityDict
    layer_height: QuantityDict
    scan_velocity: QuantityDict
    temperature_preheat: QuantityDict


class BuildParameters(QuantityModel):
    """
    Build configurations utilized for solver and process map.
    """

    beam_diameter: QuantityField = DEFAULT["beam_diameter"]
    beam_power: QuantityField = DEFAULT["beam_power"]
    hatch_spacing: QuantityField = DEFAULT["hatch_spacing"]
    layer_height: QuantityField = DEFAULT["layer_height"]
    scan_velocity: QuantityField = DEFAULT["scan_velocity"]
    temperature_preheat: QuantityField = DEFAULT["temperature_preheat"]
