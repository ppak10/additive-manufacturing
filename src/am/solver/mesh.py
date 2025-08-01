import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F

from matplotlib.collections import QuadMesh
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from datetime import datetime
from pathlib import Path
from pint import Quantity
from scipy.ndimage import gaussian_filter
from torch.types import Number, Tensor
from torchvision.transforms.functional import gaussian_blur
from typing import Any, cast

from am.segmenter.types import Segment

from .config import SolverConfig
from .types import MeshConfig


class SolverMesh:
    def __init__(self, config: SolverConfig, mesh_config: MeshConfig):
        self.config: SolverConfig = config
        self.mesh_config: MeshConfig = mesh_config

        self.x: float
        self.y: float
        self.z: float

        self.x_index: int
        self.y_index: int
        self.z_index: int

        self.x_range: Tensor = torch.Tensor()
        self.y_range: Tensor = torch.Tensor()
        self.z_range: Tensor = torch.Tensor()

        self.x_range_centered: Tensor = torch.Tensor()
        self.y_range_centered: Tensor = torch.Tensor()
        self.z_range_centered: Tensor = torch.Tensor()

        self.grid: Tensor = torch.Tensor()

    def initialize_grid(
        self, fill_value: Number, device: str = "cpu", dtype=torch.float32
    ) -> Tensor:

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

        # Initial and current locations for x, y, z within the mesh
        self.x = cast(float, self.mesh_config.x_initial.to("meter").magnitude)
        self.y = cast(float, self.mesh_config.y_initial.to("meter").magnitude)
        self.z = cast(float, self.mesh_config.z_initial.to("meter").magnitude)

        # Index of x, y, and z locations within the mesh
        self.x_index = int(round((self.x - x_start) / x_step))
        self.y_index = int(round((self.y - y_start) / y_step))
        self.z_index = int(round((self.z - z_start) / z_step))

        self.grid = torch.full(
            (len(self.x_range), len(self.y_range), len(self.z_range)),
            fill_value,
            device=device,
            dtype=dtype,
        )

        return self.grid

    def diffuse(
        self,
        delta_time: Quantity,
        diffusivity: Quantity,
        grid_offset: float,
        mode: str = "gaussian_convolution",
    ) -> None:
        """
        Performs diffusion on `self.grid` over time delta.
        Primarily intended for temperature based values.
        """

        device = "cpu"

        dt = cast(float, delta_time.to("s").magnitude)

        if dt <= 0:
            # Diffuse not valid if delta time is 0.
            return

        # Expects thermal diffusivity
        D = cast(float, diffusivity.to("m**2/s").magnitude)

        x_step = cast(float, self.mesh_config.x_step.to("m").magnitude)
        y_step = cast(float, self.mesh_config.y_step.to("m").magnitude)
        z_step = cast(float, self.mesh_config.z_step.to("m").magnitude)

        # Wolfer et al. Section 2.2
        diffuse_sigma = cast(float, (2 * D * dt) ** 0.5)

        # Compute padding values
        pad_x = max(int((4 * diffuse_sigma) // (x_step * 2)), 1)
        pad_y = max(int((4 * diffuse_sigma) // (y_step * 2)), 1)
        pad_z = max(int((4 * diffuse_sigma) // (z_step * 2)), 1)

        padding = (pad_z, pad_z, pad_y, pad_y, pad_x, pad_x)

        # Meant to normalize temperature values around 0 by removing preheat.
        grid_normalized = self.grid - grid_offset

        # Unsqueeze to account for batch dimension
        # https://github.com/pytorch/pytorch/issues/72521#issuecomment-1090350222
        grid_normalized = grid_normalized.unsqueeze(0)

        # Mirror padding
        grid_padded = F.pad(grid_normalized, padding, mode="reflect")

        # Squeeze back to remove batch dimension
        grid_padded = grid_padded.squeeze()

        # Boundary conditions
        # Temperature Boundary Condition (2019 Wolfer et al. Figure 3b)
        if self.mesh_config.boundary_condition == "temperature":
            # X and Y values are flipped alongside boundary condition
            grid_padded[-pad_x:, :, :] *= -1
            grid_padded[:pad_x, :, :] *= -1
            grid_padded[:, -pad_y:, :] *= -1
            grid_padded[:, :pad_y, :] *= -1
            grid_padded[:, :, :pad_z] *= -1
            grid_padded[:, :, -pad_z:] *= 1

        # Flux Boundary Condition (2019 Wolfer et al. Figure 3a)
        # TODO: Double check this
        if self.mesh_config.boundary_condition == "flux":
            # X and Y values are mirrored alongside boundary condition
            grid_padded[-pad_x:, :, :] = grid_padded[-2 * pad_x : -pad_x, :, :]
            grid_padded[:pad_x, :, :] = grid_padded[pad_x : 2 * pad_x, :, :]
            grid_padded[:, -pad_y:, :] = grid_padded[:, -2 * pad_y : -pad_y, :]
            grid_padded[:, :pad_y, :] = grid_padded[:, pad_y : 2 * pad_y, :]
            grid_padded[:, :, -pad_z:] = grid_padded[:, :, -(2 * pad_z) : -pad_z]
            grid_padded[:, :, :pad_z] = grid_padded[:, :, pad_z : 2 * pad_z]

        # Apply Gaussian smoothing
        sigma = diffuse_sigma / z_step

        match mode:
            case "gaussian_filter":
                grid_filtered = gaussian_filter(grid_padded.cpu(), sigma=sigma)
                grid_filtered = torch.tensor(grid_filtered).to(device)

                # Crop out the padded areas.
                grid_cropped = grid_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]

            case "gaussian_blur":
                # Doesn't seem to work properly, don't use
                # sigma = torch.tensor(diffuse_sigma / self.mesh["z_step"])
                kernel_size = 5
                grid_filtered = gaussian_blur(
                    grid_padded, kernel_size=[kernel_size, kernel_size], sigma=sigma
                )

                # Crop out the padded areas.
                grid_cropped = grid_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]

            case "gaussian_convolution":
                # Create a 3D Gaussian kernel
                kernel_size = int(4 * sigma) | 1  # Ensure kernel size is odd
                kernel_size = max(3, kernel_size)
                x = (
                    torch.arange(kernel_size, dtype=torch.float32, device=device)
                    - (kernel_size - 1) / 2
                )
                g = torch.exp(-(x**2) / (2 * sigma**2))
                g /= g.sum()
                kernel_3d = torch.einsum("i,j,k->ijk", g, g, g).to(grid_padded.dtype)
                kernel = kernel_3d.unsqueeze(0).unsqueeze(0)

                grid_filtered = F.conv3d(
                    grid_padded.unsqueeze(0), kernel, padding=0
                ).squeeze(0)

                # Crop the padded area
                grid_cropped = grid_filtered
            case _:
                raise Exception(f"'{mode}' model not found")

        # Re-add in the preheat temperature values
        self.grid = torch.Tensor(grid_cropped) + grid_offset

    def update_xy(self, segment: Segment, mode: str = "absolute") -> None:
        """
        Method to update location via command
        @param segment
        @param mode: "global" for next xy, or "relative" for distance and phi
        """
        match mode:
            case "absolute":
                # Updates using prescribed GCode positions in segment.
                # This limits potential drift caused by rounding to mesh indexes

                x_next = cast(float, segment.x_next.to("m").magnitude)
                y_next = cast(float, segment.y_next.to("m").magnitude)

                x_step = cast(float, self.mesh_config.x_step.to("m").magnitude)
                y_step = cast(float, self.mesh_config.y_step.to("m").magnitude)

                x_start = cast(float, self.mesh_config.x_start.to("m").magnitude)
                y_start = cast(float, self.mesh_config.y_start.to("m").magnitude)

                next_x_index = round((x_next - x_start) / x_step)
                next_y_index = round((y_next - y_start) / y_step)

                self.x, self.y = x_next, y_next
                self.x_index, self.y_index = next_x_index, next_y_index

            case "relative":
                # Updates relative to `phi` and `dt` values
                # Can potentially drift results if
                # TODO: Implement
                # dt = segment["distance_xy"] / self.build["velocity"]
                pass

    # TODO: Move to its own class and implement properly for edge and corner cases
    def graft(self, theta: torch.Tensor, grid_offset: float) -> None:
        x_offset, y_offset = len(self.x_range) // 2, len(self.y_range) // 2

        # Calculate roll amounts
        x_roll = round(-x_offset + self.x_index)
        y_roll = round(-y_offset + self.y_index)

        # Update prev_theta using torch.roll and subtract background temperature
        roll = (
            torch.roll(theta, shifts=(x_roll, y_roll, 0), dims=(0, 1, 2)) - grid_offset
        )
        self.grid += roll

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

    def visualize_2D(
        self,
        cmap: str = "plasma",
        include_axis: bool = True,
        label: str = "Temperature (K)",
        vmin: float = 300,
        vmax: float | None = None,
        transparent: bool = False,
        units: str = "mm",
    ) -> tuple[Figure, Axes, QuadMesh]:
        """
        2D Rendering methods mesh using matplotlib.
        """
        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        # x_range and y_range are computed this way to avoid incorrect list
        # length issues during unit conversion.
        x_range = [Quantity(x, "m").to(units).magnitude for x in self.x_range]
        y_range = [Quantity(y, "m").to(units).magnitude for y in self.y_range]

        ax.set_xlim(x_range[0], x_range[-1])
        ax.set_ylim(y_range[0], y_range[-1])

        top_view = self.grid[:, :, -1].T

        if transparent:
            data = np.ma.masked_where(top_view <= vmin, top_view)
        else:
            data = top_view

        mesh = ax.pcolormesh(x_range, y_range, data, cmap=cmap, vmin=vmin, vmax=vmax)
        mesh.set_alpha(1.0)

        if transparent:
            mesh.set_array(data)
            mesh.set_antialiased(False)

        if not include_axis:
            _ = ax.axis("off")
        else:
            ax.set_xlabel(units)
            ax.set_ylabel(units)
            fig.colorbar(mesh, ax=ax, label=label)

        return fig, ax, mesh

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
