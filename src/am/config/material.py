from typing_extensions import cast, TypedDict
from pint import Quantity
from pintdantic import QuantityDict, QuantityInput, QuantityModel, QuantityField
from pydantic import BaseModel

DEFAULT = {
    "name": "Stainless Steel 316L",
    "specific_heat_capacity": (455, "joules / (kilogram * kelvin)"),
    "absorptivity": (1.0, "dimensionless"),
    "thermal_conductivity": (8.9, "watts / (meter * kelvin)"),
    "density": (7910, "kilogram / (meter) ** 3"),
    "temperature_melt": (1673, "kelvin"),
    "temperature_liquidus": (1710.26, "kelvin"),
    "temperature_solidus": (1683.68, "kelvin"),
}


class MaterialDict(TypedDict):
    name: str
    # Specific Heat Capacity at Constant Pressure (J ⋅ kg^-1 ⋅ K^-1)
    specific_heat_capacity: QuantityDict

    # Absorptivity (Unitless)
    absorptivity: QuantityDict

    # Thermal Conductivity (W / (m ⋅ K))
    thermal_conductivity: QuantityDict

    # # Density (kg / m^3)
    density: QuantityDict

    # Melting Temperature (K)
    temperature_melt: QuantityDict

    # Liquidus Temperature (K)
    temperature_liquidus: QuantityDict

    # Solidus Temperature (K)
    temperature_solidus: QuantityDict


class MaterialInput(BaseModel):
    specific_heat_capacity: QuantityInput | None = DEFAULT["specific_heat_capacity"]
    absorptivity: QuantityInput | None = DEFAULT["absorptivity"]
    thermal_conductivity: QuantityInput | None = DEFAULT["thermal_conductivity"]
    density: QuantityInput | None = DEFAULT["density"]
    temperature_melt: QuantityInput | None = DEFAULT["temperature_melt"]
    temperature_liquidus: QuantityInput | None = DEFAULT["temperature_liquidus"]
    temperature_solidus: QuantityInput | None = DEFAULT["temperature_solidus"]


class Material(QuantityModel):
    """
    Build configurations utilized for solver and process map.
    """

    name: str = DEFAULT["name"]
    specific_heat_capacity: QuantityField = DEFAULT["specific_heat_capacity"]
    absorptivity: QuantityField = DEFAULT["absorptivity"]
    thermal_conductivity: QuantityField = DEFAULT["thermal_conductivity"]
    density: QuantityField = DEFAULT["density"]
    temperature_melt: QuantityField = DEFAULT["temperature_melt"]
    temperature_liquidus: QuantityField = DEFAULT["temperature_liquidus"]
    temperature_solidus: QuantityField = DEFAULT["temperature_solidus"]

    @property
    def thermal_diffusivity(self) -> Quantity:
        thermal_conductivity = cast(Quantity, self.thermal_conductivity)
        density = cast(Quantity, self.density)
        specific_heat_capacity = cast(Quantity, self.specific_heat_capacity)

        # Thermal Diffusivity (Wolfer et al. Equation 1)
        return thermal_conductivity / (density * specific_heat_capacity)
