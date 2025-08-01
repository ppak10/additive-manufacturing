import json

from pathlib import Path
from pint import Quantity, UnitRegistry
from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator,
    field_serializer,
    ValidationError,
)
from typing import cast, ClassVar, Literal, TypedDict

# TODO: Make a class for handling quantity for these configs to inherit from.


# TypedDict for Quantity serialized as dict
class QuantityDict(TypedDict):
    magnitude: float
    units: str


####################
# Material Configs #
####################


class MaterialConfigDict(TypedDict):
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

    # https://www.researchgate.net/figure/Liquidus-and-solidus-temperatures-of-316L-SS-and-304-SS_tbl3_353416408
    # Liquidus Temperature (K)
    temperature_liquidus: QuantityDict

    # Solidus Temperature (K)
    temperature_solidus: QuantityDict


class MaterialConfig(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    name: str
    specific_heat_capacity: Quantity
    absorptivity: Quantity
    thermal_conductivity: Quantity
    density: Quantity
    temperature_melt: Quantity
    temperature_liquidus: Quantity
    temperature_solidus: Quantity

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @field_serializer(
        "specific_heat_capacity",
        "absorptivity",
        "thermal_conductivity",
        "density",
        "temperature_melt",
        "temperature_liquidus",
        "temperature_solidus",
    )
    def serialize_quantity(self, value: Quantity) -> QuantityDict:
        if isinstance(value, Quantity):
            return self._quantity_to_dict(value)
        return QuantityDict(magnitude=0.0, units="unknown")

    @classmethod
    def create_default(cls, ureg: UnitRegistry) -> "MaterialConfig":
        return cls(
            name="Stainless Steel 316L",
            specific_heat_capacity=cast(
                Quantity, ureg.Quantity(455, "joules / (kilogram * kelvin)")
            ),
            absorptivity=cast(Quantity, ureg.Quantity(1.0, "dimensionless")),
            thermal_conductivity=cast(
                Quantity, ureg.Quantity(8.9, "watts / (meter * kelvin)")
            ),
            density=cast(Quantity, ureg.Quantity(7910, "kilogram / (meter) ** 3")),
            temperature_melt=cast(Quantity, ureg.Quantity(1673, "kelvin")),
            temperature_liquidus=cast(Quantity, ureg.Quantity(1710.26, "kelvin")),
            temperature_solidus=cast(Quantity, ureg.Quantity(1683.68, "kelvin")),
        )

    def to_dict(self) -> MaterialConfigDict:
        return {
            "name": self.name,
            "specific_heat_capacity": self._quantity_to_dict(
                self.specific_heat_capacity
            ),
            "absorptivity": self._quantity_to_dict(self.absorptivity),
            "thermal_conductivity": self._quantity_to_dict(self.thermal_conductivity),
            "density": self._quantity_to_dict(self.density),
            "temperature_melt": self._quantity_to_dict(self.temperature_melt),
            "temperature_liquidus": self._quantity_to_dict(self.temperature_liquidus),
            "temperature_solidus": self._quantity_to_dict(self.temperature_solidus),
        }

    @property
    def thermal_diffusivity(self) -> Quantity:
        # Thermal Diffusivity (Wolfer et al. Equation 1)
        return self.thermal_conductivity / (self.density * self.specific_heat_capacity)

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return Quantity(d["magnitude"], d["units"])

    @field_validator(
        "specific_heat_capacity",
        "absorptivity",
        "thermal_conductivity",
        "density",
        "temperature_melt",
        "temperature_liquidus",
        "temperature_solidus",
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
    def from_dict(cls, data: MaterialConfigDict) -> "MaterialConfig":
        return cls(**data)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "MaterialConfig":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        else:
            raise ValueError(
                f"Unexpected JSON structure in {path}: expected dict or list of dicts"
            )


#################
# Build Configs #
#################


class BuildConfigDict(TypedDict):
    beam_diameter: QuantityDict
    beam_power: QuantityDict
    scan_velocity: QuantityDict
    temperature_preheat: QuantityDict


class BuildConfig(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    beam_diameter: Quantity
    beam_power: Quantity
    scan_velocity: Quantity
    temperature_preheat: Quantity

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @field_serializer(
        "beam_diameter",
        "beam_power",
        "scan_velocity",
        "temperature_preheat",
    )
    def serialize_quantity(self, value: Quantity) -> QuantityDict:
        if isinstance(value, Quantity):
            return self._quantity_to_dict(value)
        return QuantityDict(
            magnitude=0.0,
            units="unknown",
        )

    @classmethod
    def create_default(cls, ureg: UnitRegistry) -> "BuildConfig":
        return cls(
            beam_diameter=cast(Quantity, ureg.Quantity(5e-5, "meter")),
            beam_power=cast(Quantity, ureg.Quantity(200, "watts")),
            scan_velocity=cast(Quantity, ureg.Quantity(0.8, "meter / second")),
            temperature_preheat=cast(Quantity, ureg.Quantity(300, "kelvin")),
        )

    def to_dict(self) -> BuildConfigDict:
        return {
            "beam_diameter": self._quantity_to_dict(self.beam_diameter),
            "beam_power": self._quantity_to_dict(self.beam_power),
            "scan_velocity": self._quantity_to_dict(self.scan_velocity),
            "temperature_preheat": self._quantity_to_dict(self.temperature_preheat),
        }

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return Quantity(d["magnitude"], d["units"])

    @field_validator(
        "beam_diameter",
        "beam_power",
        "scan_velocity",
        "temperature_preheat",
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
    def from_dict(cls, data: BuildConfigDict) -> "BuildConfig":
        return cls(**data)

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "BuildConfig":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        else:
            raise ValueError(
                f"Unexpected JSON structure in {path}: expected dict or list of dicts"
            )


################
# Mesh Configs #
################


class MeshConfigDict(TypedDict):
    x_step: QuantityDict
    y_step: QuantityDict
    z_step: QuantityDict

    # Boundaries
    x_min: QuantityDict
    x_max: QuantityDict
    y_min: QuantityDict
    y_max: QuantityDict
    z_min: QuantityDict
    z_max: QuantityDict

    # Initial x, y, and z locations
    x_initial: QuantityDict
    y_initial: QuantityDict
    z_initial: QuantityDict

    # Padding
    x_start_pad: QuantityDict
    y_start_pad: QuantityDict
    z_start_pad: QuantityDict
    x_end_pad: QuantityDict
    y_end_pad: QuantityDict
    z_end_pad: QuantityDict

    # Boundary Condition Behavior
    boundary_condition: Literal["flux", "temperature"]


class MeshConfig(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)
    # Dimensional Step Size
    x_step: Quantity
    y_step: Quantity
    z_step: Quantity

    # Boundaries
    x_min: Quantity
    x_max: Quantity
    y_min: Quantity
    y_max: Quantity
    z_min: Quantity
    z_max: Quantity

    # Initial x, y, and z locations
    x_initial: Quantity
    y_initial: Quantity
    z_initial: Quantity

    # Padding
    x_start_pad: Quantity
    y_start_pad: Quantity
    z_start_pad: Quantity
    x_end_pad: Quantity
    y_end_pad: Quantity
    z_end_pad: Quantity

    # Boundary Condition Behavior
    boundary_condition: Literal["flux", "temperature"]

    @field_serializer(
        "x_step",
        "y_step",
        "z_step",
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "z_min",
        "z_max",
        "x_initial",
        "y_initial",
        "z_initial",
        "x_start_pad",
        "y_start_pad",
        "z_start_pad",
        "x_end_pad",
        "y_end_pad",
        "z_end_pad",
    )
    def serialize_quantity(self, value: Quantity) -> QuantityDict:
        if isinstance(value, Quantity):
            return self._quantity_to_dict(value)
        return QuantityDict(
            magnitude=0.0,
            units="unknown",
        )

    @staticmethod
    def _quantity_to_dict(q: Quantity) -> QuantityDict:
        return {"magnitude": cast(float, q.magnitude), "units": str(q.units)}

    @property
    def x_start(self) -> Quantity:
        return self.x_min - self.x_start_pad

    @property
    def x_end(self) -> Quantity:
        return cast(Quantity, self.x_max + self.x_end_pad)

    @property
    def y_start(self) -> Quantity:
        return self.y_min - self.y_start_pad

    @property
    def y_end(self) -> Quantity:
        return cast(Quantity, self.y_max + self.y_end_pad)

    @property
    def z_start(self) -> Quantity:
        return self.z_min - self.z_start_pad

    @property
    def z_end(self) -> Quantity:
        return cast(Quantity, self.z_max + self.z_end_pad)

    # @staticmethod
    # def _dict_to_quantity(d: QuantityDict, ureg: UnitRegistry) -> Quantity:
    #     # Create Quantity from magnitude and units string
    #     return cast(Quantity, ureg.Quantity(d["magnitude"], d["units"]))
    #
    # @field_validator(
    #     "x_step",
    #     "y_step",
    #     "z_step",
    #     "x_min",
    #     "x_max",
    #     "y_min",
    #     "y_max",
    #     "z_min",
    #     "z_max",
    #     "x_initial",
    #     "y_initial",
    #     "z_initial",
    #     "x_start_pad",
    #     "y_start_pad",
    #     "z_start_pad",
    #     "x_end_pad",
    #     "y_end_pad",
    #     "z_end_pad",
    #     mode="before"
    # )
    # def parse_quantity(cls, v: Quantity) -> Quantity:
    #     # if isinstance(v, dict):
    #     #     # Strict check keys and types
    #     #     expected_keys = {"magnitude", "units"}
    #     #     if set(v.keys()) != expected_keys:
    #     #         raise ValidationError(f"Invalid keys for QuantityDict, expected {expected_keys} but got {v.keys()}")
    #     #     if not isinstance(v["magnitude"], float):
    #     #         raise ValidationError(f"QuantityDict magnitude must be float, got {type(v['magnitude'])}")
    #     #     if not isinstance(v["units"], str):
    #     #         raise ValidationError(f"QuantityDict units must be str, got {type(v['units'])}")
    #     #     return cls._dict_to_quantity(v, ureg)
    #     if isinstance(v, Quantity):
    #         return v
    #     else:
    #         raise ValidationError(f"Expected Quantity, got {type(v)}")

    @staticmethod
    def _dict_to_quantity(d: QuantityDict) -> Quantity:
        # Create Quantity from magnitude and units string
        return Quantity(d["magnitude"], d["units"])

    @field_validator(
        "x_step",
        "y_step",
        "z_step",
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "z_min",
        "z_max",
        "x_initial",
        "y_initial",
        "z_initial",
        "x_start_pad",
        "y_start_pad",
        "z_start_pad",
        "x_end_pad",
        "y_end_pad",
        "z_end_pad",
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

    def to_dict(self) -> MeshConfigDict:
        return {
            "x_step": self._quantity_to_dict(self.x_step),
            "y_step": self._quantity_to_dict(self.y_step),
            "z_step": self._quantity_to_dict(self.z_step),
            "x_min": self._quantity_to_dict(self.x_min),
            "x_max": self._quantity_to_dict(self.x_max),
            "y_min": self._quantity_to_dict(self.y_min),
            "y_max": self._quantity_to_dict(self.y_max),
            "z_min": self._quantity_to_dict(self.z_min),
            "z_max": self._quantity_to_dict(self.z_max),
            "x_initial": self._quantity_to_dict(self.x_initial),
            "y_initial": self._quantity_to_dict(self.y_initial),
            "z_initial": self._quantity_to_dict(self.z_initial),
            "x_start_pad": self._quantity_to_dict(self.x_start_pad),
            "y_start_pad": self._quantity_to_dict(self.y_start_pad),
            "z_start_pad": self._quantity_to_dict(self.z_start_pad),
            "x_end_pad": self._quantity_to_dict(self.x_end_pad),
            "y_end_pad": self._quantity_to_dict(self.y_end_pad),
            "z_end_pad": self._quantity_to_dict(self.z_end_pad),
            "boundary_condition": self.boundary_condition,
        }

    @classmethod
    def from_dict(cls, data: MeshConfigDict) -> "MeshConfig":
        return cls(**data)

    @classmethod
    def create_default(cls, ureg: UnitRegistry) -> "MeshConfig":
        return cls(
            x_step=cast(Quantity, ureg.Quantity(25, "micrometer")),
            y_step=cast(Quantity, ureg.Quantity(25, "micrometer")),
            z_step=cast(Quantity, ureg.Quantity(25, "micrometer")),
            # Boundaries
            x_min=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            x_max=cast(Quantity, ureg.Quantity(10.0, "millimeter")),
            y_min=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            y_max=cast(Quantity, ureg.Quantity(10.0, "millimeter")),
            z_min=cast(Quantity, ureg.Quantity(-0.8, "millimeter")),
            z_max=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            # Initial x, y, and z locations
            x_initial=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            y_initial=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            z_initial=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            # Padding
            x_start_pad=cast(Quantity, ureg.Quantity(0.2, "millimeter")),
            y_start_pad=cast(Quantity, ureg.Quantity(0.2, "millimeter")),
            z_start_pad=cast(Quantity, ureg.Quantity(0.0, "millimeter")),
            x_end_pad=cast(Quantity, ureg.Quantity(0.2, "millimeter")),
            y_end_pad=cast(Quantity, ureg.Quantity(0.2, "millimeter")),
            z_end_pad=cast(Quantity, ureg.Quantity(0.1, "millimeter")),
            # Boundary Condition Behavior
            boundary_condition="temperature",
        )

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))
        return path

    @classmethod
    def load(cls, path: Path) -> "MeshConfig":
        with path.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return cls.from_dict(data)
        else:
            raise ValueError(
                f"Unexpected JSON structure in {path}: expected dict or list of dicts"
            )
