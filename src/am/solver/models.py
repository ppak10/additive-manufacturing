import numpy as np
import torch

from am import data
from torchvision.transforms.functional import gaussian_blur
from importlib.resources import files
from scipy import integrate

# Small non-zero value for integration and other purposes
# FLOOR = 10**-3  # Float16
FLOOR = 10**-7  # Float32


class SolverModels:
    """
    Class for solver models such as Eagar-Tsai and Rosenthal.
    """

    def __init__(self):
        # Stores temperature fields by power and velocity.
        self.model_cache = {
            # (power, velocity): tensor([[[]]])
        }

    def eagar_tsai(self, dt, phi, num=None):
        """
        Provides next state for eagar tsai modeling
        """
        alpha = self.absorptivity
        c_p = self.specific_heat_capacity
        D = self.thermal_diffusivity
        pi = np.pi
        rho = self.density
        sigma = self.beam_diameter / 4

        p = self.power
        v = self.velocity

        t_0 = self.temperature_preheat

        # Coefficient for Equation 16 in Wolfer et al.
        coefficient = alpha * p / (2 * pi * sigma**2 * rho * c_p * pi ** (3 / 2))

        # Initial temperature mesh for solver
        theta = np.ones((len(self.X_c), len(self.Y_c), len(self.Z_c))) * t_0

        X = self.X_c[:, None, None, None]
        Y = self.Y_c[None, :, None, None]
        Z = self.Z_c[None, None, :, None]

        def integral(tau):
            x_travel, y_travel = -v * tau * np.cos(phi), -v * tau * np.sin(phi)

            lmbda = np.sqrt(4 * D * tau)
            gamma = np.sqrt(2 * sigma**2 + lmbda**2)
            start = (4 * D * tau) ** (-3 / 2)

            # Free Template Solution
            # Wolfer et al. Equation A.3
            termy = sigma * lmbda * np.sqrt(2 * pi) / (gamma)
            yexp1 = np.exp(-1 * ((Y.cpu() - y_travel) ** 2) / gamma**2)
            yintegral = termy * np.array(yexp1)

            # Wolfer et al. Equation A.2
            termx = termy
            xexp1 = np.exp(-1 * ((X.cpu() - x_travel) ** 2) / gamma**2)
            xintegral = termx * np.array(xexp1)

            # Wolfer et al. Equation 18
            zintegral = np.array(2 * np.exp(-(Z.cpu() ** 2) / (4 * D * tau)))

            # Wolfer et al. Equation 16
            value = coefficient * start * xintegral * yintegral * zintegral

            return value

        if num is None:
            # Splits prescribed delta time into into minimum increments of 10**-4 s.
            num = max(1, int(dt // 10**-4))

        # Note: torch.trapz does not seem to produce accurate results.
        integration = integrate.fixed_quad(integral, FLOOR, dt, n=num)
        # integration = integrate.fixed_quad(integral, FLOOR, dt, n=75)
        # print(np.unique(integration[0]))

        return torch.tensor(theta + integration[0]).to(self.device)

    def rosenthal(self, dt, phi, num=None):
        """
        Provides next state for rosenthal modeling
        """
        alpha = self.absorptivity
        D = self.thermal_diffusivity
        k = self.thermal_conductivity
        pi = np.pi

        p = self.power
        v = self.velocity

        t_0 = self.temperature_preheat
        t_l = self.temperature_liquidus
        t_s = self.temperature_solidus

        X, Y, Z = torch.meshgrid(self.X_c, self.Y_c, self.Z_c, indexing="ij")

        # Initial temperature mesh for solver
        theta_shape = (len(self.X_c), len(self.Y_c), len(self.Z_c))
        theta = torch.ones(theta_shape, device=self.device) * t_0

        coefficient = alpha * p / (2 * pi * k)

        if num is None:
            # Splits prescribed delta time into into minimum increments of 10**-4 s.
            num = max(1, int(dt // 10**-4))

        # For longer segments, since no heat diffusion is applied, it seems like
        # its a long segment of instantenously heated material.
        for tau in torch.linspace(0, dt, steps=num, device=self.device):
            # Adds in the expected distance traveled along global x and y axes.
            x_travel, y_travel = -v * tau * np.cos(phi), -v * tau * np.sin(phi)

            # Assuming x is along the weld center line
            zeta = -(X - x_travel)

            # r is the cylindrical radius composed of y and z
            r = torch.sqrt((Y - y_travel) ** 2 + Z**2)

            # Rotate the reference frame for Rosenthal by phi
            # Counterclockwise
            # https://en.wikipedia.org/wiki/Rotation_matrix#In_two_dimensions
            if phi > 0:
                zeta_rot = zeta * np.cos(phi) - r * np.sin(phi)
                r_rot = zeta * np.sin(phi) + r * np.cos(phi)

            # Clockwise
            # https://en.wikipedia.org/wiki/Rotation_matrix#Direction
            else:
                zeta_rot = zeta * np.cos(phi) + r * np.sin(phi)
                r_rot = -zeta * np.sin(phi) + r * np.cos(phi)

            # Prevent `nan` values with minimum floor value.
            min_R = torch.tensor(FLOOR)

            R = torch.max(torch.sqrt(zeta_rot**2 + r_rot**2), min_R)

            # Rosenthal temperature contribution
            # `notes/rosenthal/#shape_of_temperature_field`
            temp = (coefficient / R) * torch.exp((v * (zeta_rot - R)) / (2 * D))

            ########################
            # Temperature Clamping #
            ########################
            # TODO #1: Revisit this and see if there's a better solution.
            # Current implementation of rosenthal's equation seems to result in
            # temperatures much higher than melting and results in extreme
            # amounts of heat build up.

            # Prevents showing temperatures above liquidus
            temp = torch.minimum(temp, torch.tensor(t_l))

            # Mask temperatures close to background to prevent "long tail"
            temp[temp < t_s] = 0

            # Add contribution to the temperature field
            theta += temp

        return theta

    # TODO: Simplify to be a huggingface abstraction
    def surrogate_ss316(self, dt, phi, num=None):
        model_timestep = 98  # Generates predictions according to last timestep.
        phi = torch.tensor(phi)
        t_0 = self.temperature_preheat  # Original model implementation has 293.
        t_l = self.temperature_liquidus
        t_s = self.temperature_solidus
        t_max = 6500

        p = self.power
        v = self.velocity * 1000

        prep_x = lambda x: torch.as_tensor(
            x / np.array([500, 1500, 100]), dtype=torch.float
        )

        if (self.power, self.velocity) in self.model_cache:
            # Load existing model calculations if already in cache.
            prediction = self.model_cache[(self.power, self.velocity)]
        elif p > 0:
            # Otherwise load model and generate inference.
            model_path = files(data).joinpath("solver", "model", "ss316.pkl")
            model_weights = torch.load(model_path)
            model = Generator3d(**MODEL_KWARGS)
            model.load_state_dict(model_weights)
            model = model.to(self.device)
            model.eval()

            # Disable gradient computation for all parameters
            for param in model.parameters():
                param.requires_grad = False

            x = prep_x([p, v, model_timestep]).unsqueeze(0).to(self.device)
            output = model(x)

            # TODO: Implement varying downsampling based on mesh size
            # output = output
            output_size = (
                output.shape[2] // 10,
                output.shape[3] // 10,
                output.shape[4] // 10,
            )
            # print(output.shape, output_size)

            # Downsample from 10 micron scale to 100 micron scale
            downsampled = F.adaptive_avg_pool3d(output, output_size=output_size)
            # downsampled = output

            normalized = t_0 + (t_max - t_0) * downsampled
            prediction = normalized.squeeze()

            # Cache prediction
            self.model_cache[(self.power, self.velocity)] = prediction
        else:
            theta_shape = (len(self.X_c), len(self.Y_c), len(self.Z_c))
            theta = torch.ones(theta_shape, device=self.device, dtype=self.dtype) * t_0
            return theta

        # Initial temperature mesh for solver
        theta_shape = (len(self.X_c), len(self.Y_c), len(self.Z_c))
        theta = torch.ones(theta_shape, device=self.device, dtype=self.dtype) * t_0

        # return theta
        # Rotate the reference frame for Rosenthal by phi
        # Counterclockwise
        # https://en.wikipedia.org/wiki/Rotation_matrix#In_two_dimensions
        if phi > 0:
            R = torch.tensor(
                [
                    [torch.cos(phi), -torch.sin(phi), 0],
                    [torch.sin(phi), torch.cos(phi), 0],
                    [0, 0, 1],
                ],
                device=self.device,
                dtype=self.dtype,
            )

        # Clockwise
        # https://en.wikipedia.org/wiki/Rotation_matrix#Direction
        else:
            R = torch.tensor(
                [
                    [torch.cos(phi), torch.sin(phi), 0],
                    [-torch.sin(phi), torch.cos(phi), 0],
                    [0, 0, 1],
                ],
                device=self.device,
                dtype=self.dtype,
            )

        # Create a normalized coordinate grid
        X, Y, Z = torch.meshgrid(self.X_c, self.Y_c, self.Z_c, indexing="ij")

        # Flatten meshgrid tensors
        X_flat = X.flatten()
        Y_flat = Y.flatten()
        Z_flat = Z.flatten()

        # Stack into shape (3, N)
        coords = torch.stack([X_flat, Y_flat, Z_flat], dim=0)

        # Apply rotation
        rotated_coords = R @ coords  # Matrix multiplication

        # Reshape back to original shape
        X_rot = rotated_coords[0].reshape(X.shape)
        Y_rot = rotated_coords[1].reshape(Y.shape)
        Z_rot = rotated_coords[2].reshape(Z.shape)

        if num is None:
            # Splits prescribed delta time into into minimum increments of 10**-4 s.
            num = max(1, int(dt // 10**-4))

        # For longer segments, since no heat diffusion is applied, it seems like
        # its a long segment of instantenously heated material.
        for tau in torch.linspace(0, dt, steps=num, device=self.device):
            temp = torch.zeros(theta_shape, device=self.device, dtype=self.dtype)

            # Compute the center position in (x, y)
            x_start = theta_shape[0] // 2 - prediction.shape[0] // 2
            y_start = theta_shape[1] // 2 - prediction.shape[1] // 2
            z_top = theta_shape[2]  # Top

            # Paste the downsampled tensor
            temp[
                x_start : x_start + prediction.shape[0],
                y_start : y_start + prediction.shape[1],
                z_top - prediction.shape[2] : z_top,
            ] = prediction

            distance = tau * self.velocity

            # Distance traveled in x and y directions
            x_travel = distance * torch.cos(phi)
            y_travel = distance * torch.sin(phi)

            # Translate the rotated coordinates by the distance
            X_rot += x_travel
            Y_rot += y_travel

            # Assume theta has shape (W, H, D)
            temp_rot = temp.permute(2, 1, 0)  # Now (D, H, W)

            # Add batch and channel dimensions (N=1, C=1)
            temp_rot = temp_rot.unsqueeze(0).unsqueeze(0)  # Shape: (1, 1, D, H, W)

            # Normalize rotated coordinates to [-1, 1]
            X_rot_norm = 2 * (X_rot - X_rot.min()) / (X_rot.max() - X_rot.min()) - 1
            Y_rot_norm = 2 * (Y_rot - Y_rot.min()) / (Y_rot.max() - Y_rot.min()) - 1
            Z_rot_norm = 2 * (Z_rot - Z_rot.min()) / (Z_rot.max() - Z_rot.min()) - 1

            # Stack into grid format (1, D, H, W, 3)
            grid = torch.stack([X_rot_norm, Y_rot_norm, Z_rot_norm], dim=-1).unsqueeze(
                0
            )

            # Interpolate using grid_sample
            temp_rot = F.grid_sample(
                temp_rot, grid, align_corners=True, mode="bilinear"
            )

            # Remove batch & channel dims -> back to (D, H, W)
            temp = temp_rot.squeeze(0).squeeze(0)

            # # Prevents showing temperatures above liquidus
            # temp = torch.minimum(temp, torch.tensor(t_l))

            # # Mask temperatures close to background to prevent "long tail"
            # temp[temp < t_s] = 0

            # # Add contribution to the temperature field
            theta += temp

            # theta += temp_rot

        return theta

        # # print(theta.shape)
        # if num is None:
        #     # Splits prescribed delta time into into minimum increments of 10**-4 s.
        #     num = max(1, int(dt // 10**-4))

        # for tau in torch.linspace(0, dt, steps=num, device=self.device):
        #     # print(f'{tau}')
        #     distance = tau * self.velocity
        #     temp = rotate_translate(theta, phi, distance, device=self.device)

        #     ########################
        #     # Temperature Clamping #
        #     ########################
        #     # TODO #1: Revisit this and see if there's a better solution.
        #     # Current implementation of rosenthal's equation seems to result in
        #     # temperatures much higher than melting and results in extreme
        #     # amounts of heat build up.

        #     # Prevents showing temperatures above liquidus
        #     temp = torch.minimum(temp, torch.tensor(t_l))

        #     # Mask temperatures close to background to prevent "long tail"
        #     temp[temp < t_s] = 0

        #     # Add contribution to the temperature field
        #     theta += temp

        return theta


def rotate_translate(theta, phi, distance, device):
    # Distance traveled in x and y directions
    x_travel = distance * torch.cos(phi)
    y_travel = distance * torch.sin(phi)

    # Create meshgrid for rotation (only considering 2D x and y)
    x = torch.arange(theta.shape[0], device=device).float()  # x-coordinates
    y = torch.arange(theta.shape[1], device=device).float()  # y-coordinates
    X, Y = torch.meshgrid(
        x, y, indexing="ij"
    )  # specify 'ij' or 'xy' depending on your needs

    # Apply rotation (counterclockwise)
    X_rot = X * torch.cos(phi) - Y * torch.sin(phi)
    Y_rot = X * torch.sin(phi) + Y * torch.cos(phi)

    # Translate the rotated coordinates by the distance
    X_rot += x_travel
    Y_rot += y_travel

    # Indices for the rotated and translated tensor
    # Clip to ensure they remain within bounds
    X_rot = X_rot.clamp(0, theta.shape[0] - 1).long()
    Y_rot = Y_rot.clamp(0, theta.shape[1] - 1).long()

    # Create a new tensor for the result after rotation and translation
    rotated_theta = torch.zeros_like(theta)

    # Assign values based on the rotated indices
    for i in range(theta.shape[0]):
        for j in range(theta.shape[1]):
            rotated_theta[X_rot[i, j], Y_rot[i, j]] = theta[i, j]

    return rotated_theta


# -*- coding: utf-8 -*-
"""
@author: AmirPouya Hemmasian (ahemmasi@andrew.cmu.edu)
"""
import torch
import torch.nn.functional as F
from torch import nn
import numpy as np

MODEL_KWARGS = {
    "channels": [128, 64, 32, 16, 8, 4],
    "fc_hiddens": [],
    "shape": (128, 64, 64),
    "slices": [slice(26, -27, None), slice(7, -7, None), slice(12, -13, None)],
    "up_kwargs": {"kernel_size": 4, "padding": 1, "stride": 2},
}


def upsample(c_in, c_out, up_kwargs, act=nn.LeakyReLU):

    if "mode" in up_kwargs:
        layers = [
            nn.Upsample(**up_kwargs),
            nn.Conv3d(c_in, c_out, 3, padding="same", padding_mode="replicate"),
        ]
    else:
        layers = [nn.ConvTranspose3d(c_in, c_out, **up_kwargs)]

    layers += [act()]
    return nn.Sequential(*layers)


class Generator3d(nn.Module):

    def __init__(
        self,
        shape=(128, 32, 64),
        fc_hiddens=[],
        channels=[128, 64, 32, 16, 8, 4],
        up_kwargs=dict(scale_factor=2, mode="trilinear", align_corners=False),
        act=nn.LeakyReLU,
        slices=3 * [slice(None, None)],
    ):

        super().__init__()
        # print(shape, fc_hiddens, channels, slices)
        self.slice_x, self.slice_y, self.slice_z = slices
        #######################################################################
        cd = 2 ** (len(channels) - 1)
        c1 = channels[0] if channels else 1
        d1, d2, d3 = shape
        self.start_shape = (c1, d1 // cd, d2 // cd, d3 // cd)

        fc_layers = []
        fc_units = [3] + fc_hiddens + [np.prod(self.start_shape)]
        for i in range(len(fc_units) - 1):
            fc_layers += [nn.Linear(fc_units[i], fc_units[i + 1]), act()]
        self.fcn = nn.Sequential(*fc_layers)
        #######################################################################
        conv_layers = []
        for i in range(len(channels) - 1):
            conv_layers += [upsample(channels[i], channels[i + 1], up_kwargs, act)]
        conv_layers += [
            nn.Conv3d(channels[-1], 1, 3, padding="same", padding_mode="replicate")
        ]
        self.cnn = nn.Sequential(*conv_layers)

    def forward(self, u, mask=False):
        # print(u.shape, *self.start_shape)
        x = self.fcn(u).reshape(u.shape[0], *self.start_shape)
        # print(f"x.shape {x.shape}")
        x = self.cnn(x)
        # print(f"x.shape {x.shape}")
        x = x[:, :, self.slice_x, self.slice_y, self.slice_z]
        # print(f"x.shape {x.shape}")
        if mask:
            return torch.sigmoid(x)
        return F.leaky_relu(x, 0.001 if self.training else 0)
