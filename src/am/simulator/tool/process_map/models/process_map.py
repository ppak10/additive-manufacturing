import numpy as np

from pathlib import Path
from pint import Quantity
from pydantic import BaseModel, computed_field, PrivateAttr
from typing_extensions import cast, TypedDict
from tqdm.rich import tqdm

from am.config import BuildParameters, BuildParametersDict, Material, MaterialDict

from .process_map_parameter_range import (
    ProcessMapParameterRange,
    ProcessMapParameterRangeDict,
)
from .process_map_data_point import ProcessMapDataPoint
from .process_map_parameter import ProcessMapParameter


class ProcessMapDict(TypedDict):
    build_parameters: BuildParametersDict
    material: MaterialDict

    parameter_ranges: list[ProcessMapParameterRangeDict]
    out_path: Path


class ProcessMap(BaseModel):
    """
    Process Map class for generating lack of fusion predictions of material.
    """

    build_parameters: BuildParameters
    material: Material

    parameter_ranges: list[ProcessMapParameterRange]
    out_path: Path

    # Private field to cache data points
    _data_points: list[ProcessMapDataPoint] | None = PrivateAttr(default=None)

    @computed_field
    @property
    def data_points(self) -> list[ProcessMapDataPoint]:
        """
        Generate all data points from the parameter ranges using a cartesian product.
        Caches the result after first generation or loading from file.

        Returns:
            List of ProcessMapDataPoint objects with all parameter combinations.
        """
        # If we have cached data points, return those
        if self._data_points is not None:
            return self._data_points

        # Otherwise, generate from parameter ranges
        from itertools import product

        # Build arrays of values for each parameter range
        ranges = []
        names = []
        units = []

        for parameter_range in self.parameter_ranges:
            # Generate numpy array of values from start to stop with step
            step = cast(Quantity, parameter_range.step).magnitude
            start = cast(Quantity, parameter_range.start).magnitude

            # Add half step to include stop
            stop = cast(Quantity, parameter_range.stop).magnitude + step / 2
            values = np.arange(start, stop, step)

            ranges.append(values)
            names.append(parameter_range.name)
            units.append(parameter_range.units)

        # Generate cartesian product of all parameter values
        data_points = []
        for combination in product(*ranges):
            parameters = []

            for name, value, unit in zip(names, combination, units):
                # Create ProcessMapParameter with the value and units from the range
                param = ProcessMapParameter(
                    name=name, value=cast(Quantity, Quantity(value, unit))
                )
                parameters.append(param)

            # Create data point with these parameters
            data_point = ProcessMapDataPoint(
                parameters=parameters, melt_pool_dimensions=None, labels=None
            )
            data_points.append(data_point)

        # Cache the generated data points
        self._data_points = data_points
        return data_points

    def save(self, file_path: Path | None = None) -> Path:
        """
        Save process map configuration to JSON file.

        Args:
            file_path: Optional path to save

        Returns:
            Path to the saved configuration file
        """
        if file_path is None:
            file_path = self.out_path / "process_map.json"

        with open(file_path, "w") as f:
            f.write(self.model_dump_json(indent=2))

        return file_path

    @classmethod
    def load(cls, file_path: Path, progress_callback=None) -> "ProcessMap":
        """
        Load process map configuration from JSON file.

        Args:
            file_path: Path to the process_map.json file
            progress_callback: Optional progress callback to attach

        Returns:
            Process map instance with loaded configuration
        """
        import json

        with open(file_path, "r") as f:
            data = json.load(f)

        # Convert out_path string back to Path
        if "out_path" in data:
            data["out_path"] = Path(data["out_path"])

        # Extract data_points if present (will be loaded into private field)
        loaded_data_points = None
        if "data_points" in data:
            loaded_data_points = [
                ProcessMapDataPoint.model_validate(dp) for dp in data["data_points"]
            ]
            # Remove from data since it's not a direct field
            del data["data_points"]

        process_map = cls.model_validate(data)

        # Set the loaded data points
        if loaded_data_points is not None:
            process_map._data_points = loaded_data_points

        # if progress_callback is not None:
        #     slicer.progress_callback = progress_callback

        return process_map
