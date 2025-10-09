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

from am.segmenter.types import Segment
from am.schema import MeshParameters
from .gaussian import gaussian_blur_3d

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

    def initialize_grid(self, mesh_parameters: MeshParameters, fill_value: float, dtype=jnp.float32) -> Array:

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
        boundary_condition = "temperature"
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
        pad_x = max(int(4 * sigma_x), 1)
        pad_y = max(int(4 * sigma_y), 1)
        pad_z = max(int(4 * sigma_z), 1)

        # padding = (pad_z, pad_z, pad_y, pad_y, pad_x, pad_x)
        padding = ((pad_x, pad_x), (pad_y, pad_y), (pad_z, pad_z))

        # Meant to normalize temperature values around 0 by removing preheat.
        grid_normalized = self.grid - grid_offset

        # Unsqueeze to account for batch dimension
        # https://github.com/pytorch/pytorch/issues/72521#issuecomment-1090350222
        # grid_normalized = grid_normalized.unsqueeze(0)

        # Mirror padding
        grid_padded = jnp.pad(grid_normalized, padding, mode="reflect")

        # Squeeze back to remove batch dimension
        # grid_padded = grid_padded.squeeze()

        # Boundary conditions
        # Temperature Boundary Condition (2019 Wolfer et al. Figure 3b)
        if boundary_condition == "temperature":
            # X and Y values are flipped alongside boundary condition
            # grid_padded[-pad_x:, :, :] *= -1
            # grid_padded[:pad_x, :, :] *= -1
            # grid_padded[:, -pad_y:, :] *= -1
            # grid_padded[:, :pad_y, :] *= -1
            # grid_padded[:, :, :pad_z] *= -1
            # grid_padded[:, :, -pad_z:] *= 1
            grid_padded = grid_padded.at[-pad_x:, :, :].set(-grid_padded[-pad_x:, :, :])
            grid_padded = grid_padded.at[:pad_x, :, :].set(-grid_padded[:pad_x, :, :])
            grid_padded = grid_padded.at[:, -pad_y:, :].set(-grid_padded[:, -pad_y:, :])
            grid_padded = grid_padded.at[:, :pad_y, :].set(-grid_padded[:, :pad_y, :])
            grid_padded = grid_padded.at[:, :, :pad_z].set(-grid_padded[:, :, :pad_z])
            grid_padded = grid_padded.at[:, :, -pad_z:].set(grid_padded[:, :, -pad_z:])

        # Flux Boundary Condition (2019 Wolfer et al. Figure 3a)
        # TODO: Double check this
        if boundary_condition == "flux":
            # X and Y values are mirrored alongside boundary condition
            # grid_padded[-pad_x:, :, :] = grid_padded[-2 * pad_x : -pad_x, :, :]
            # grid_padded[:pad_x, :, :] = grid_padded[pad_x : 2 * pad_x, :, :]
            # grid_padded[:, -pad_y:, :] = grid_padded[:, -2 * pad_y : -pad_y, :]
            # grid_padded[:, :pad_y, :] = grid_padded[:, pad_y : 2 * pad_y, :]
            # grid_padded[:, :, -pad_z:] = grid_padded[:, :, -(2 * pad_z) : -pad_z]
            # grid_padded[:, :, :pad_z] = grid_padded[:, :, pad_z : 2 * pad_z]

            grid_padded = grid_padded.at[-pad_x:, :, :].set(-grid_padded[-2 * pad_x:-pad_x, :, :])
            grid_padded = grid_padded.at[:pad_x, :, :].set(-grid_padded[pad_x:2 * pad_x, :, :])
            grid_padded = grid_padded.at[:, -pad_y:, :].set(-grid_padded[:, -2 * pad_y: -pad_y, :])
            grid_padded = grid_padded.at[:, :pad_y, :].set(-grid_padded[:, pad_y : 2 * pad_y, :])
            grid_padded = grid_padded.at[:, :, :pad_z].set(-grid_padded[:, :, -(2 * pad_z) : -pad_z])
            grid_padded = grid_padded.at[:, :, -pad_z:].set(grid_padded[:, :, pad_z: 2 * pad_z])

        # Apply Gaussian smoothing
        # sigma = diffuse_sigma / z_step
        sigma = float(jnp.mean(jnp.array([sigma_x, sigma_y, sigma_z])))

        blurred = gaussian_blur_3d(grid_padded, sigma=sigma, padding="SAME")

        # match mode:
        #     case "gaussian_filter":
        #         grid_filtered = gaussian_filter(grid_padded, sigma=sigma)
        #         # grid_filtered = torch.tensor(grid_filtered).to(device)
        #
        #         # Crop out the padded areas.
        #         grid_cropped = grid_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]
        #
        #     case "gaussian_blur":
        #         # Doesn't seem to work properly, don't use
        #         pass
        #         # sigma = torch.tensor(diffuse_sigma / self.mesh["z_step"])
        #         # kernel_size = 5
        #         # grid_filtered = gaussian_blur(
        #         #     grid_padded, kernel_size=[kernel_size, kernel_size], sigma=sigma
        #         # )
        #
        #         # Crop out the padded areas.
        #         # grid_cropped = grid_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]
        #
        #     case "gaussian_convolution":
        #         # Create a 3D Gaussian kernel
        #         pass
        #         # kernel_size = int(4 * sigma) | 1  # Ensure kernel size is odd
        #         # kernel_size = max(3, kernel_size)
        #         # x = (
        #         #     torch.arange(kernel_size, dtype=torch.float32, device=device)
        #         #     - (kernel_size - 1) / 2
        #         # )
        #         # g = torch.exp(-(x**2) / (2 * sigma**2))
        #         # g /= g.sum()
        #         # kernel_3d = torch.einsum("i,j,k->ijk", g, g, g).to(grid_padded.dtype)
        #         # kernel = kernel_3d.unsqueeze(0).unsqueeze(0)
        #         #
        #         # grid_filtered = F.conv3d(
        #         #     grid_padded.unsqueeze(0), kernel, padding=0
        #         # ).squeeze(0)
        #         #
        #         # # Crop the padded area
        #         # grid_cropped = grid_filtered
        #     case _:
        #         raise Exception(f"'{mode}' model not found")

        grid_cropped = blurred[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]


        # Re-add in the preheat temperature values
        self.grid = grid_cropped + grid_offset

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
        roll = (
            jnp.roll(theta, shift=(x_roll, y_roll, 0), axis=(0, 1, 2)) - grid_offset
        )
        self.grid = self.grid + roll

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)

        # data = {
        #     "config": self.config.model_dump(),
        #     "mesh_config": self.mesh_config.to_dict(),
        #     "x_range": self.x_range.cpu(),
        #     "y_range": self.y_range.cpu(),
        #     "z_range": self.z_range.cpu(),
        #     "x_range_centered": self.x_range_centered.cpu(),
        #     "y_range_centered": self.y_range_centered.cpu(),
        #     "z_range_centered": self.z_range_centered.cpu(),
        #     "grid": self.grid.cpu(),
        # }
        #
        # torch.save(data, path)

        np.savez_compressed(
            path,
            # config=self.config.model_dump(),
            # mesh_config=self.mesh_config.to_dict(),
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
        # data: dict[str, Any] = torch.load(path, map_location="cpu")
        data = np.load(path, allow_pickle=True)

        # config = SolverConfig(**data["config"].item())
        # mesh_config = MeshConfig.from_dict(data["mesh_config"])

        instance = cls()
        # instance = cls(config, mesh_config)
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
