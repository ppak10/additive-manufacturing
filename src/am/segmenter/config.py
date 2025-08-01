from pint import UnitRegistry
from pathlib import Path
from pydantic import BaseModel, model_validator, PrivateAttr
from typing import Literal


class SegmenterConfig(BaseModel):
    # Subset of units systems from `dir(ureg.sys)`
    ureg_default_system: Literal["cgs", "mks"] = "cgs"
    segmenter_path: Path | None = None
    verbose: bool | None = False

    _ureg: UnitRegistry = PrivateAttr()

    @model_validator(mode="after")
    def init_ureg(self) -> "SegmenterConfig":
        self._ureg = UnitRegistry()
        self._ureg.default_system = self.ureg_default_system
        return self

    @property
    def ureg(self) -> UnitRegistry:
        return self._ureg

    def save(self, path: Path | None = None) -> Path:
        """
        Save the configuration to a YAML file.
        If no path is given, saves to '<workspace_path>/config.yaml'.
        """
        if path is None:
            if not self.segmenter_path:
                raise ValueError("solver_path must be set to determine save location.")
            path = self.segmenter_path / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))

        return path

    @classmethod
    def load(cls: type["SegmenterConfig"], path: Path) -> "SegmenterConfig":
        if not path.exists():
            raise FileNotFoundError(f"Config file not found at {path}")

        return cls.model_validate_json(path.read_text())
