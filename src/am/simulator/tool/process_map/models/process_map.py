from pathlib import Path
from pydantic import BaseModel
from typing_extensions import TypedDict
from tqdm.rich import tqdm

from am.config import BuildParameters, BuildParametersDict, Material, MaterialDict

from .process_map_parameter_range import (
    ProcessMapParameterRange,
    ProcessMapParameterRangeDict,
)


class ProcessMapDict(TypedDict):
    build_parameters: BuildParametersDict
    material: MaterialDict

    parameters: list[ProcessMapParameterRangeDict]
    out_path: Path


class ProcessMap(BaseModel):
    """
    Process Map class for generating lack of fusion predictions of material.
    """

    build_parameters: BuildParameters
    material: Material

    parameter_ranges: list[ProcessMapParameterRange]
    out_path: Path

    # def run(self, num_proc: int = 1) -> ProcessMapPoints:
    #     points = []
    #
    #     if num_proc <= 1:
    #
    #         # Iterates through points z (inner) -> y (middle) -> x (outer)
    #         for point in tqdm(process_map.points, desc="Running simulations"):
    #             # Copies build parameters to a new object to pass as overrides.
    #             modified_build_parameters = deepcopy(build_parameters)
    #
    #             for index, parameter in enumerate(process_map.parameters):
    #                 modified_build_parameters.__setattr__(parameter, point[index])
    #
    #             point = run_process_map_point(modified_build_parameters, material)
    #
    #             points.append(point)
    #     else:
    #         # Multi-process execution
    #         args_list = []
    #
    #         for point in process_map.points:
    #             # Copies build parameters to a new object to pass as overrides.
    #             modified_build_parameters = deepcopy(build_parameters)
    #
    #             for index, parameter in enumerate(process_map.parameters):
    #                 modified_build_parameters.__setattr__(parameter, point[index])
    #
    #             args = (modified_build_parameters, material)
    #             args_list.append(args)
    #
    #         with ProcessPoolExecutor(max_workers=num_proc) as executor:
    #             futures = []
    #             for args in args_list:
    #                 future = executor.submit(run_process_map_point, *args)
    #                 futures.append(future)
    #
    #             # Use tqdm to track progress
    #             for future in tqdm(
    #                 as_completed(futures), total=len(futures), desc="Running simulations"
    #             ):
    #                 result = future.result()  # This will raise any exceptions that occurred
    #                 points.append(result)
    #
    #     process_map_points = ProcessMapPoints(
    #         parameters=process_map.parameters, points=points
    #     )
    #
    #     process_map_points.save(process_map_path / "points.json")
    #
    #     return process_map_points

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

        process_map = cls.model_validate(data)
        # if progress_callback is not None:
        #     slicer.progress_callback = progress_callback

        return process_map
