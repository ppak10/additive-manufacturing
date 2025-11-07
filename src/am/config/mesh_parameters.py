from pint import Quantity
from pintdantic import QuantityDict, QuantityInput, QuantityModel, QuantityField
from pydantic import BaseModel
from typing_extensions import cast, Literal, TypedDict

DEFAULT = {
    "x_step": (25, "micrometer"),
    "y_step": (25, "micrometer"),
    "z_step": (25, "micrometer"),
    "x_min": (0.0, "millimeter"),
    "x_max": (10.0, "millimeter"),
    "y_min": (0.0, "millimeter"),
    "y_max": (10.0, "millimeter"),
    "z_min": (-0.8, "millimeter"),
    "z_max": (0.0, "millimeter"),
    "x_initial": (0.0, "millimeter"),
    "y_initial": (0.0, "millimeter"),
    "z_initial": (0.0, "millimeter"),
    "x_start_pad": (0.2, "millimeter"),
    "y_start_pad": (0.2, "millimeter"),
    "z_start_pad": (0.0, "millimeter"),
    "x_end_pad": (0.2, "millimeter"),
    "y_end_pad": (0.2, "millimeter"),
    "z_end_pad": (0.1, "millimeter"),
}


class MeshParametersDict(TypedDict):
    x_step: QuantityDict
    y_step: QuantityDict
    z_step: QuantityDict
    x_min: QuantityDict
    x_max: QuantityDict
    y_min: QuantityDict
    y_max: QuantityDict
    z_min: QuantityDict
    z_max: QuantityDict
    x_initial: QuantityDict
    y_initial: QuantityDict
    z_initial: QuantityDict
    x_start_pad: QuantityDict
    y_start_pad: QuantityDict
    z_start_pad: QuantityDict
    x_end_pad: QuantityDict
    y_end_pad: QuantityDict
    z_end_pad: QuantityDict
    boundary_condition: Literal["flux", "temperature"]


class MeshParametersInput(BaseModel):
    """Mesh parameters configuration"""

    x_step: QuantityInput | None = DEFAULT["x_step"]
    y_step: QuantityInput | None = DEFAULT["y_step"]
    z_step: QuantityInput | None = DEFAULT["z_step"]
    x_min: QuantityInput | None = DEFAULT["x_min"]
    x_max: QuantityInput | None = DEFAULT["x_max"]
    y_min: QuantityInput | None = DEFAULT["y_min"]
    y_max: QuantityInput | None = DEFAULT["y_max"]
    z_min: QuantityInput | None = DEFAULT["z_min"]
    z_max: QuantityInput | None = DEFAULT["z_max"]
    x_initial: QuantityInput | None = DEFAULT["x_initial"]
    y_initial: QuantityInput | None = DEFAULT["y_initial"]
    z_initial: QuantityInput | None = DEFAULT["z_initial"]
    x_start_pad: QuantityInput | None = DEFAULT["x_start_pad"]
    y_start_pad: QuantityInput | None = DEFAULT["y_start_pad"]
    z_start_pad: QuantityInput | None = DEFAULT["z_start_pad"]
    x_end_pad: QuantityInput | None = DEFAULT["x_end_pad"]
    y_end_pad: QuantityInput | None = DEFAULT["y_end_pad"]
    z_end_pad: QuantityInput | None = DEFAULT["z_end_pad"]
    boundary_condition: str | None = "temperature"


class MeshParameters(QuantityModel):
    """
    Mesh configurations utilized for solver and process map.
    """

    x_step: QuantityField = DEFAULT["x_step"]
    y_step: QuantityField = DEFAULT["y_step"]
    z_step: QuantityField = DEFAULT["z_step"]
    x_min: QuantityField = DEFAULT["x_min"]
    x_max: QuantityField = DEFAULT["x_max"]
    y_min: QuantityField = DEFAULT["y_min"]
    y_max: QuantityField = DEFAULT["y_max"]
    z_min: QuantityField = DEFAULT["z_min"]
    z_max: QuantityField = DEFAULT["z_max"]
    x_initial: QuantityField = DEFAULT["x_initial"]
    y_initial: QuantityField = DEFAULT["y_initial"]
    z_initial: QuantityField = DEFAULT["z_initial"]
    x_start_pad: QuantityField = DEFAULT["x_start_pad"]
    y_start_pad: QuantityField = DEFAULT["y_start_pad"]
    z_start_pad: QuantityField = DEFAULT["z_start_pad"]
    x_end_pad: QuantityField = DEFAULT["x_end_pad"]
    y_end_pad: QuantityField = DEFAULT["y_end_pad"]
    z_end_pad: QuantityField = DEFAULT["z_end_pad"]
    boundary_condition: Literal["flux", "temperature"] = "temperature"

    @property
    def x_start(self) -> Quantity:
        x_min = cast(Quantity, self.x_min)
        x_start_pad = cast(Quantity, self.x_start_pad)
        return x_min - x_start_pad

    @property
    def x_end(self) -> Quantity:
        x_max = cast(Quantity, self.x_max)
        x_end_pad = cast(Quantity, self.x_end_pad)
        return cast(Quantity, x_max + x_end_pad)

    @property
    def y_start(self) -> Quantity:
        y_min = cast(Quantity, self.y_min)
        y_start_pad = cast(Quantity, self.y_start_pad)
        return cast(Quantity, y_min - y_start_pad)

    @property
    def y_end(self) -> Quantity:
        y_max = cast(Quantity, self.y_max)
        y_end_pad = cast(Quantity, self.y_end_pad)
        return cast(Quantity, y_max + y_end_pad)

    @property
    def z_start(self) -> Quantity:
        z_min = cast(Quantity, self.z_min)
        z_start_pad = cast(Quantity, self.z_start_pad)
        return cast(Quantity, z_min - z_start_pad)

    @property
    def z_end(self) -> Quantity:
        z_max = cast(Quantity, self.z_max)
        z_end_pad = cast(Quantity, self.z_end_pad)
        return cast(Quantity, z_max + z_end_pad)
