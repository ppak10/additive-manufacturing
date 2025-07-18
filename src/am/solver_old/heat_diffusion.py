import numpy as np
import torch
import torch.nn.functional as F

from scipy.ndimage import gaussian_filter
from torchvision.transforms.functional import gaussian_blur


class SolverHeatDiffusion:
    """
    Class for modeling heat diffusion from a source using torch.
    """

    def diffuse(self, dt, mode="gaussian_convolution"):
        """
        Diffuses heat of `self.theta` of the previous timestep with time delta.
        """

        D = self.thermal_diffusivity

        # Wolfer et al. Section 2.2
        diffuse_sigma = np.sqrt(2 * D * dt)

        # Compute padding values
        pad_x = max(int((4 * diffuse_sigma) // (self.x_step * 2)), 1)
        pad_y = max(int((4 * diffuse_sigma) // (self.y_step * 2)), 1)
        pad_z = max(int((4 * diffuse_sigma) // (self.z_step * 2)), 1)

        padding = (pad_z, pad_z, pad_y, pad_y, pad_x, pad_x)
        theta_minus_t_0 = self.temperatures - self.temperature_preheat

        # Unsqueeze to account for batch dimension
        # https://github.com/pytorch/pytorch/issues/72521#issuecomment-1090350222
        theta_minus_t_0 = theta_minus_t_0.unsqueeze(0)

        # Mirror padding
        theta_padded = F.pad(theta_minus_t_0, padding, mode="reflect")

        # Squeeze back to remove batch dimension
        theta_padded = theta_padded.squeeze()

        # Handle boundary conditions
        # Temperature Boundary Condition (2019 Wolfer et al. Figure 3b)
        if self.boundary_condition == "temperature":
            # X and Y values are flipped alongside boundary condition
            theta_padded[-pad_x:, :, :] *= -1
            theta_padded[:pad_x, :, :] *= -1
            theta_padded[:, -pad_y:, :] *= -1
            theta_padded[:, :pad_y, :] *= -1
            theta_padded[:, :, :pad_z] *= -1
            theta_padded[:, :, -pad_z:] *= 1

        # Flux Boundary Condition (2019 Wolfer et al. Figure 3a)
        # TODO: Double check this
        if self.boundary_condition == "flux":
            # X and Y values are mirrored alongside boundary condition
            theta_padded[-pad_x:, :, :] = theta_padded[-2 * pad_x : -pad_x, :, :]
            theta_padded[:pad_x, :, :] = theta_padded[pad_x : 2 * pad_x, :, :]
            theta_padded[:, -pad_y:, :] = theta_padded[:, -2 * pad_y : -pad_y, :]
            theta_padded[:, :pad_y, :] = theta_padded[:, pad_y : 2 * pad_y, :]
            theta_padded[:, :, -pad_z:] = theta_padded[:, :, -(2 * pad_z) : -pad_z]
            theta_padded[:, :, :pad_z] = theta_padded[:, :, pad_z : 2 * pad_z]

        # Apply Gaussian smoothing
        sigma = diffuse_sigma / self.z_step
        # sigma = 2

        match mode:
            case "gaussian_filter":
                theta_padded_cpu = theta_padded.cpu()
                theta_filtered = gaussian_filter(theta_padded_cpu, sigma=sigma)
                theta_filtered = torch.tensor(theta_filtered).to(self.device)

                # Crop out the padded areas.
                theta_cropped = theta_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]

            case "gaussian_blur":
                # Doesn't seem to work properly, don't use
                # sigma = torch.tensor(diffuse_sigma / self.mesh["z_step"])
                kernel_size = 5
                theta_filtered = gaussian_blur(
                    theta_padded, kernel_size=[kernel_size, kernel_size], sigma=sigma
                )

                # Crop out the padded areas.
                theta_cropped = theta_filtered[pad_x:-pad_x, pad_y:-pad_y, pad_z:-pad_z]

            case "gaussian_convolution":
                # Create a 3D Gaussian kernel
                kernel_size = int(4 * sigma) | 1  # Ensure kernel size is odd
                kernel_size = max(3, kernel_size)
                x = (
                    torch.arange(kernel_size, dtype=torch.float32, device=self.device)
                    - (kernel_size - 1) / 2
                )
                g = torch.exp(-(x**2) / (2 * sigma**2))
                g /= g.sum()
                kernel_3d = torch.einsum("i,j,k->ijk", g, g, g).to(theta_padded.dtype)
                kernel = kernel_3d.unsqueeze(0).unsqueeze(0)

                theta_filtered = F.conv3d(
                    theta_padded.unsqueeze(0), kernel, padding=0
                ).squeeze(0)

                # Crop the padded area
                theta_cropped = theta_filtered
            case _:
                print(f"'{mode}' model not found")

        # Re-add in the preheat temperature values
        theta = theta_cropped + self.temperature_preheat

        return theta
