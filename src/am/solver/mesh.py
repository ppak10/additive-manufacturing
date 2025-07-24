import torch

from pathlib import Path
from typing import Any, cast
from torch.types import Number, Tensor

from .config import SolverConfig
from .types import MeshConfig

class SolverMesh:
    def __init__(self, config: SolverConfig, mesh_config: MeshConfig):
        self.config: SolverConfig = config
        self.mesh_config: MeshConfig = mesh_config

        self.x_range: Tensor = torch.Tensor() 
        self.y_range: Tensor = torch.Tensor() 
        self.z_range: Tensor = torch.Tensor() 

        self.x_range_centered: Tensor = torch.Tensor()
        self.y_range_centered: Tensor = torch.Tensor()
        self.z_range_centered: Tensor = torch.Tensor()

        self.grid: Tensor = torch.Tensor()

    def initialize_grid(self, fill_value: Number, device: str = "cpu", dtype = torch.float32) -> Tensor:

        x_start = cast(float, self.mesh_config.x_start.to("meter").magnitude)
        x_step = cast(float, self.mesh_config.x_step.to("meter").magnitude)
        x_end = cast(float, self.mesh_config.x_end.to("meter").magnitude)

        self.x_range = torch.arange(x_start, x_end, x_step, device=device, dtype=dtype)

        y_start = cast(float, self.mesh_config.y_start.to("meter").magnitude)
        y_step = cast(float, self.mesh_config.y_step.to("meter").magnitude)
        y_end = cast(float, self.mesh_config.y_end.to("meter").magnitude)

        self.y_range = torch.arange(y_start, y_end, y_step, device=device, dtype=dtype)

        z_start = cast(float, self.mesh_config.z_start.to("meter").magnitude)
        z_step = cast(float, self.mesh_config.z_step.to("meter").magnitude)
        z_end = cast(float, self.mesh_config.z_end.to("meter").magnitude)

        self.z_range = torch.arange(z_start, z_end, z_step, device=device, dtype=dtype)

        # Centered x, y, and z coordinates for use in solver models
        self.x_range_centered = self.x_range - self.x_range[len(self.x_range) // 2]
        self.y_range_centered = self.y_range - self.y_range[len(self.y_range) // 2]
        self.z_range_centered = self.z_range

        self.grid = torch.full(
            (len(self.x_range), len(self.y_range), len(self.z_range)),
            fill_value,
            device=device,
            dtype=dtype,
        )

        return self.grid

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "config": self.config.model_dump(),
            "mesh_config": self.mesh_config.to_dict(),
            "x_range": self.x_range.cpu(),
            "y_range": self.y_range.cpu(),
            "z_range": self.z_range.cpu(),
            "x_range_centered": self.x_range_centered.cpu(),
            "y_range_centered": self.y_range_centered.cpu(),
            "z_range_centered": self.z_range_centered.cpu(),
            "grid": self.grid.cpu(),
        }

        torch.save(data, path)
        return path

    @classmethod
    def load(cls, path: Path) -> "SolverMesh":
        data: dict[str, Any] = torch.load(path, map_location="cpu")

        config = SolverConfig(**data["config"])
        mesh_config = MeshConfig.from_dict(data["mesh_config"])

        instance = cls(config, mesh_config)
        instance.x_range = data["x_range"]
        instance.y_range = data["y_range"]
        instance.z_range = data["z_range"]

        instance.x_range_centered = data["x_range_centered"]
        instance.y_range_centered = data["y_range_centered"]
        instance.z_range_centered = data["z_range_centered"]

        instance.grid = data["grid"]
        return instance

