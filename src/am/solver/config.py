from pint import UnitRegistry
from pathlib import Path
from pydantic import BaseModel, model_validator, PrivateAttr
from typing import Literal


class SolverConfig(BaseModel):
    # Subset of units systems from `dir(ureg.sys)`
    ureg_default_system: Literal["cgs", "mks"] = "cgs"
    solver_path: Path | None = None

    _ureg: UnitRegistry = PrivateAttr()

    @property
    def ureg(self) -> UnitRegistry:
        return self._ureg

    @model_validator(mode="after")
    def initialize(self) -> "SolverConfig":
        self._ureg = UnitRegistry()
        self._ureg.default_system = self.ureg_default_system

        return self

    def save(self, path: Path | None = None) -> Path:
        if path is None:
            if not self.solver_path:
                raise ValueError("solver_path must be set to determine save location.")
            path = self.solver_path / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))

        return path

    @classmethod
    def load(cls: type["SolverConfig"], path: Path) -> "SolverConfig":
        if not path.exists():
            raise FileNotFoundError(f"Config file not found at {path}")

        return cls.model_validate_json(path.read_text())
