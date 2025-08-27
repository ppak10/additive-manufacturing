from pint import Quantity

from typing_extensions import cast, TypedDict

from .quantity import QuantityDict, QuantityModel

class BuildParametersDict(TypedDict):
    beam_diameter: QuantityDict
    beam_power: QuantityDict
    scan_velocity: QuantityDict
    temperature_preheat: QuantityDict


class BuildParameters(QuantityModel):
    """
    Build configurations utilized for solver and process map.
    """

    beam_diameter: Quantity
    beam_power: Quantity
    scan_velocity: Quantity
    temperature_preheat: Quantity

    @classmethod
    def create_default(cls) -> "BuildParameters":
        return cls(
            beam_diameter=cast(Quantity, Quantity(5e-5, "meter")),
            beam_power=cast(Quantity, Quantity(200, "watts")),
            scan_velocity=cast(Quantity, Quantity(0.8, "meter / second")),
            temperature_preheat=cast(Quantity, Quantity(300, "kelvin")),
        )

