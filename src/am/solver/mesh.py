import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np

from jax import Array
from matplotlib.collections import QuadMesh
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from pathlib import Path
from pint import Quantity
from typing import cast

from am.config import MeshParameters

from .segment import SolverSegment
from .diffuse import apply_temperature_bc, apply_flux_bc, separable_gaussian_blur_3d


class SolverMesh:
    def __init__(self):

        self.x: float
        self.y: float
        self.z: float

        self.x_index: int
        self.y_index: int
        self.z_index: int

        self.x_start: float
        self.y_start: float
        self.z_start: float

        self.x_end: float
        self.y_end: float
        self.z_end: float

        self.x_step: float
        self.y_step: float
        self.z_step: float

        self.x_range: Array = jnp.array([])
        self.y_range: Array = jnp.array([])
        self.z_range: Array = jnp.array([])

        self.x_range_centered: Array = jnp.array([])
        self.y_range_centered: Array = jnp.array([])
        self.z_range_centered: Array = jnp.array([])

        self.grid: Array = jnp.array([])

    def initialize_grid(
        self, mesh_parameters: MeshParameters, fill_value: float, dtype=jnp.float32
    ) -> Array:

        self.x_start = mesh_parameters.x_start.to("meter").magnitude
        self.x_end = mesh_parameters.x_end.to("meter").magnitude
        self.x_step = cast(Quantity, mesh_parameters.x_step).to("m").magnitude

        self.x_range = jnp.arange(self.x_start, self.x_end, self.x_step, dtype=dtype)

        self.y_start = mesh_parameters.y_start.to("meter").magnitude
        self.y_end = mesh_parameters.y_end.to("meter").magnitude
        self.y_step = cast(Quantity, mesh_parameters.y_step).to("m").magnitude

        self.y_range = jnp.arange(self.y_start, self.y_end, self.y_step, dtype=dtype)

        self.z_start = mesh_parameters.z_start.to("meter").magnitude
        self.z_end = mesh_parameters.z_end.to("meter").magnitude
        self.z_step = cast(Quantity, mesh_parameters.z_step).to("m").magnitude

        self.z_range = jnp.arange(self.z_start, self.z_end, self.z_step, dtype=dtype)

        # Centered x, y, and z coordinates for use in solver models
        self.x_range_centered = self.x_range - self.x_range[len(self.x_range) // 2]
        self.y_range_centered = self.y_range - self.y_range[len(self.y_range) // 2]
        self.z_range_centered = self.z_range

        # Initial and current locations for x, y, z within the mesh
        self.x = cast(Quantity, mesh_parameters.x_initial).to("m").magnitude
        self.y = cast(Quantity, mesh_parameters.y_initial).to("m").magnitude
        self.z = cast(Quantity, mesh_parameters.z_initial).to("m").magnitude

        # Index of x, y, and z locations within the mesh
        self.x_index = int(round((self.x - self.x_start) / self.x_step))
        self.y_index = int(round((self.y - self.y_start) / self.y_step))
        self.z_index = int(round((self.z - self.z_start) / self.z_step))

        self.grid = jnp.full(
            (len(self.x_range), len(self.y_range), len(self.z_range)),
            fill_value,
            dtype=dtype,
        )

        return self.grid

    def diffuse(
        self,
        delta_time: Quantity,
        diffusivity: Quantity,
        grid_offset: float,
        boundary_condition="temperature",
    ) -> None:
        """
        Performs diffusion on `self.grid` over time delta.
        Primarily intended for temperature based values.
        """
        dt = delta_time.to("s").magnitude

        if dt <= 0:
            # Diffuse not valid if delta time is 0.
            return

        # Expects thermal diffusivity
        D = float(diffusivity.to("m**2/s").magnitude)

        # Wolfer et al. Section 2.2
        diffuse_sigma = (2 * D * dt) ** 0.5

        sigma_x = diffuse_sigma / self.x_step
        sigma_y = diffuse_sigma / self.y_step
        sigma_z = diffuse_sigma / self.z_step

        # Compute padding values
        truncate = 4.0
        pad_x = max(int(truncate * sigma_x + 0.5), 1)
        pad_y = max(int(truncate * sigma_y + 0.5), 1)
        pad_z = max(int(truncate * sigma_z + 0.5), 1)

        # padding = (pad_z, pad_z, pad_y, pad_y, pad_x, pad_x)
        # padding = ((pad_x, pad_x), (pad_y, pad_y), (pad_z, pad_z))

        # Meant to normalize temperature values around 0 by removing preheat.
        grid_normalized = self.grid - grid_offset

        # Apply boundary conditions through padding
        if boundary_condition == "temperature":
            # Dirichlet BC: T=0 at boundaries (reflected and negated)
            grid_padded = apply_temperature_bc(grid_normalized, pad_x, pad_y, pad_z)
        elif boundary_condition == "flux":
            # Neumann BC: ∂T/∂n=0 at boundaries (reflected)
            grid_padded = apply_flux_bc(grid_normalized, pad_x, pad_y, pad_z)
        else:
            raise ValueError(f"Unknown boundary condition: {boundary_condition}")

        # Apply separable Gaussian convolution (much more efficient than 3D convolution)
        grid_blurred = separable_gaussian_blur_3d(
            grid_padded, sigma_x, sigma_y, sigma_z, truncate
        )

        # Crop padded regions
        grid_cropped = grid_blurred[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]

        # Add back the background temperature
        self.grid = grid_cropped + grid_offset

    def update_xy(self, segment: SolverSegment, mode: str = "absolute") -> None:
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

                next_x_index = round((x_next - self.x_start) / self.x_step)
                next_y_index = round((y_next - self.y_start) / self.y_step)

                self.x, self.y = x_next, y_next
                self.x_index, self.y_index = next_x_index, next_y_index

            case "relative":
                # Updates relative to `phi` and `dt` values
                # Can potentially drift results if
                # TODO: Implement
                # dt = segment["distance_xy"] / self.build["velocity"]
                pass

    # TODO: Move to its own class and implement properly for edge and corner cases
    def graft(self, theta: Array, grid_offset: float) -> None:
        x_offset, y_offset = len(self.x_range) // 2, len(self.y_range) // 2

        # Calculate roll amounts
        x_roll = round(-x_offset + self.x_index)
        y_roll = round(-y_offset + self.y_index)

        # Update prev_theta using torch.roll and subtract background temperature
        roll = jnp.roll(theta, shift=(x_roll, y_roll, 0), axis=(0, 1, 2)) - grid_offset
        self.grid = self.grid + roll

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)

        np.savez_compressed(
            path,
            x_range=np.array(self.x_range),
            y_range=np.array(self.y_range),
            z_range=np.array(self.z_range),
            x_start=self.x_start,
            y_start=self.y_start,
            z_start=self.z_start,
            x_end=self.x_end,
            y_end=self.y_end,
            z_end=self.z_end,
            x_step=self.x_step,
            y_step=self.y_step,
            z_step=self.z_step,
            x_range_centered=np.array(self.x_range_centered),
            y_range_centered=np.array(self.y_range_centered),
            z_range_centered=np.array(self.z_range_centered),
            grid=np.array(self.grid),
        )
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
        x_range = [Quantity(x, "m").to(units).magnitude for x in np.array(self.x_range)]
        y_range = [Quantity(y, "m").to(units).magnitude for y in np.array(self.y_range)]

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
        data = np.load(path, allow_pickle=True)

        instance = cls()
        instance.x_range = jnp.array(data["x_range"])
        instance.y_range = jnp.array(data["y_range"])
        instance.z_range = jnp.array(data["z_range"])

        instance.x_start = data["x_start"]
        instance.y_start = data["y_start"]
        instance.z_start = data["z_start"]

        instance.x_end = data["x_end"]
        instance.y_end = data["y_end"]
        instance.z_end = data["z_end"]

        instance.x_step = data["x_step"]
        instance.y_step = data["y_step"]
        instance.z_step = data["z_step"]

        instance.x_range_centered = jnp.array(data["x_range_centered"])
        instance.y_range_centered = jnp.array(data["y_range_centered"])
        instance.z_range_centered = jnp.array(data["z_range_centered"])

        instance.grid = data["grid"]
        return instance
