# import matplotlib.pyplot as plt
# import numpy as np
# import torch
#
#
# from matplotlib.collections import QuadMesh
# from matplotlib.figure import Figure
# from matplotlib.axes import Axes
#
# from pathlib import Path
# from pint import Quantity
# from torch.types import Tensor
# from typing import Any, cast
#
# from am.segmenter.types import Segment
# from am.schema import Material
#
# from .config import SolverConfig
# from .types import MeshConfig
#
# device = "cpu"
# dtype = torch.float32
#
#
# class SolverMeasure:
#     def __init__(
#         self, config: SolverConfig, mesh_config: MeshConfig, material: Material
#     ):
#         self.config: SolverConfig = config
#         self.mesh_config: MeshConfig = mesh_config
#         self.material: Material = material
#
#         self.grid: Tensor = torch.Tensor()
#
#         x_start = cast(float, self.mesh_config.x_start.to("meter").magnitude)
#         x_step = cast(float, self.mesh_config.x_step.to("meter").magnitude)
#         x_end = cast(float, self.mesh_config.x_end.to("meter").magnitude)
#
#         self.x_range = torch.arange(x_start, x_end, x_step, device=device, dtype=dtype)
#
#         y_start = cast(float, self.mesh_config.y_start.to("meter").magnitude)
#         y_step = cast(float, self.mesh_config.y_step.to("meter").magnitude)
#         y_end = cast(float, self.mesh_config.y_end.to("meter").magnitude)
#
#         self.y_range = torch.arange(y_start, y_end, y_step, device=device, dtype=dtype)
#
#     def approximate_melt_pool_dimensions(self, segment: Segment):
#         phi = cast(float, segment.angle_xy.to("radian").magnitude)
#         distance_xy = cast(float, segment.distance_xy.to("meter").magnitude)
#         pass
#
#     def save(self, path: Path) -> Path:
#         path.parent.mkdir(parents=True, exist_ok=True)
#
#         data = {
#             "config": self.config.model_dump(),
#             "mesh_config": self.mesh_config.to_dict(),
#             "material": self.material.to_dict(),
#             "grid": self.grid.cpu(),
#         }
#
#         torch.save(data, path)
#         return path
#
#     def visualize_2D(
#         self,
#         cmap: str = "plasma",
#         include_axis: bool = True,
#         label: str = "Temperature (K)",
#         vmin: float = 300,
#         vmax: float | None = None,
#         transparent: bool = False,
#         units: str = "mm",
#     ) -> tuple[Figure, Axes, QuadMesh]:
#         """
#         2D Rendering methods mesh using matplotlib.
#         """
#         fig, ax = plt.subplots(1, 1, figsize=(10, 5))
#
#         # x_range and y_range are computed this way to avoid incorrect list
#         # length issues during unit conversion.
#         x_range = [Quantity(x, "m").to(units).magnitude for x in self.x_range]
#         y_range = [Quantity(y, "m").to(units).magnitude for y in self.y_range]
#
#         ax.set_xlim(x_range[0], x_range[-1])
#         ax.set_ylim(y_range[0], y_range[-1])
#
#         top_view = self.grid[:, :, -1].T
#
#         if transparent:
#             data = np.ma.masked_where(top_view <= vmin, top_view)
#         else:
#             data = top_view
#
#         mesh = ax.pcolormesh(x_range, y_range, data, cmap=cmap, vmin=vmin, vmax=vmax)
#         mesh.set_alpha(1.0)
#
#         if transparent:
#             mesh.set_array(data)
#             mesh.set_antialiased(False)
#
#         if not include_axis:
#             _ = ax.axis("off")
#         else:
#             ax.set_xlabel(units)
#             ax.set_ylabel(units)
#             fig.colorbar(mesh, ax=ax, label=label)
#
#         return fig, ax, mesh
#
#     @classmethod
#     def load(cls, path: Path) -> "SolverMeasure":
#         data: dict[str, Any] = torch.load(path, map_location="cpu")
#
#         config = SolverConfig(**data["config"])
#         material = Material.from_dict(data["material"])
#         mesh_config = MeshConfig.from_dict(data["mesh_config"])
#
#         instance = cls(config, mesh_config, material)
#
#         instance.grid = data["grid"]
#         return instance
