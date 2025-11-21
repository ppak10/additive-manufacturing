# TODO: Renamve this to something other than ProcessMap but something better than ProcessMapConfig.

from pint import Quantity
from pintdantic import QuantityDict, QuantityInput, QuantityModel
from pydantic import BaseModel, Field, model_serializer, model_validator
from typing_extensions import TypedDict
import numpy as np

from typing import Any, TypeVar

T = TypeVar("T", bound="ProcessMap")

MAX_PARAMETERS = 3

ParameterRange = dict[str, tuple[QuantityInput, QuantityInput, QuantityInput]]


class ProcessMapDict(TypedDict):
    """
    Dictionary output of process map class.

    args:
        parameters: Ordered list of parameters to use for points.
        points: Ordered list of parameter dictionaries for generated from a range.
    """

    parameters: list[str]
    points: list[dict[str, QuantityDict]]


class ProcessMapInput(BaseModel):
    parameter_ranges: list[ParameterRange] | None = Field(
        default=[],
        description=f"List of parameter ranges (min, max, step) for process map (Max of {MAX_PARAMETERS})",
    )


class ProcessMap(QuantityModel):
    """
    Overrides for build parameter configs
    """

    parameters: list[str] = []
    points: list[list[Quantity]] = []

    @model_validator(mode="before")
    @classmethod
    def generate_from_parameter_ranges(cls, data: Any) -> Any:
        """
        Generate parameters and points from parameter_ranges if provided.
        This validator runs before initialization, converting parameter_ranges
        into parameters and points, which are then stored in the model.
        """
        if not isinstance(data, dict):
            return data

        # If parameter_ranges is provided, generate parameters and points
        parameter_ranges = data.get("parameter_ranges")
        if parameter_ranges:
            if len(parameter_ranges) > MAX_PARAMETERS:
                raise ValueError(
                    f"Number of parameter ranges ({len(parameter_ranges)}) exceeds maximum ({MAX_PARAMETERS})"
                )

            # Extract parameter names
            parameters = []
            ranges = []

            for param_dict in parameter_ranges:
                for param_name, (min_val, max_val, step_val) in param_dict.items():
                    parameters.append(param_name)

                    # Convert to Quantity if not already
                    min_qty = cls._ensure_quantity(min_val)
                    max_qty = cls._ensure_quantity(max_val)
                    step_qty = cls._ensure_quantity(step_val)

                    # Generate range using numpy
                    values = np.arange(
                        min_qty.magnitude,
                        max_qty.magnitude
                        + step_qty.magnitude
                        / 2,  # Add small epsilon for inclusive range
                        step_qty.magnitude,
                    )

                    # Convert back to Quantity with the same units
                    ranges.append([Quantity(val, min_qty.units) for val in values])

            # Generate all combinations (Cartesian product)
            points = []
            if ranges:
                # Use numpy meshgrid for efficient Cartesian product
                grids = np.meshgrid(*[range(len(r)) for r in ranges], indexing="ij")
                for indices in zip(*[g.flat for g in grids]):
                    point = [ranges[i][idx] for i, idx in enumerate(indices)]
                    points.append(point)

            # Set parameters and points in data
            data["parameters"] = parameters
            data["points"] = points

        # Remove parameter_ranges from data so it's not stored
        data.pop("parameter_ranges", None)

        # Validate parameters length (whether from parameter_ranges or direct input)
        parameters = data.get("parameters", [])
        if len(parameters) > MAX_PARAMETERS:
            raise ValueError(
                f"Number of parameters ({len(parameters)}) exceeds maximum ({MAX_PARAMETERS})"
            )

        return data

    @staticmethod
    def _ensure_quantity(value: Any) -> Quantity:
        """Convert value to Quantity if it's not already."""
        if isinstance(value, Quantity):
            return value
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            return Quantity(value[0], value[1])
        else:
            raise ValueError(f"Cannot convert {value} to Quantity")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert ProcessMap to dictionary with proper serialization.
        This method is used by the save() function.
        """
        data = {"parameters": self.parameters, "points": []}

        # Creates a dict for each point with the parameter values.
        for point in self.points:
            point_parameters = {}

            # Converts each parameter from Quantity class to dict.
            for index, parameter in enumerate(self.parameters):
                point_parameters[parameter] = self._quantity_to_dict(point[index])
            data["points"].append(point_parameters)

        return data

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        # Use the to_dict method for consistent serialization
        return self.to_dict()

    @classmethod
    def from_dict(cls: type[T], data: dict[str, Any]) -> T:
        # Convert serialized points back to Quantity objects
        points = []
        if "points" in data and "parameters" in data:
            for point_dict in data["points"]:
                point = []
                for param in data["parameters"]:
                    if param in point_dict:
                        point.append(cls._dict_to_quantity(point_dict[param]))
                points.append(point)

        return cls(parameters=data.get("parameters", []), points=points)
