from pintdantic import QuantityDict, QuantityInput, QuantityModel, QuantityField
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

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


class BuildParametersInput(BaseModel):
    beam_diameter: QuantityInput | None = Field(
        default=DEFAULT["beam_diameter"],
        description="The diameter of the laser beam used during the build process. Affects energy density and melt pool size.",
    )
    beam_power: QuantityInput | None = Field(
        default=DEFAULT["beam_power"],
        description="Power of the laser beam in watts. Higher power increases melt pool temperature and penetration depth.",
    )
    hatch_spacing: QuantityInput | None = Field(
        default=DEFAULT["hatch_spacing"],
        description="Distance between adjacent scan vectors. Affects overlap and part density.",
    )
    layer_height: QuantityInput | None = Field(
        default=DEFAULT["layer_height"],
        description="Thickness of each powder layer applied before scanning.",
    )
    scan_velocity: QuantityInput | None = Field(
        default=DEFAULT["scan_velocity"],
        description="Speed at which the laser beam moves across the powder bed. Affects energy input and cooling rate.",
    )
    temperature_preheat: QuantityInput | None = Field(
        default=DEFAULT["temperature_preheat"],
        description="Initial temperature of the build platform or powder bed before laser scanning begins.",
    )


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
