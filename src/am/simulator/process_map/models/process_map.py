from pathlib import Path
from pydantic import BaseModel
from typing_extensions import TypedDict

from am.config import BuildParameters, BuildParametersDict, Material, MaterialDict

from .process_map_parameters import ProcessMapParameter, ProcessMapParameterDict


class ProcessMapDict(TypedDict):
    build_parameters: BuildParametersDict
    material: MaterialDict

    parameters: list[ProcessMapParameterDict]
    out_path: Path


class ProcessMap(BaseModel):
    """
    Process Map class for generating lack of fusion predictions of material.
    """

    build_parameters: BuildParameters
    material: Material

    parameters: list[ProcessMapParameter]
    out_path: Path

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
