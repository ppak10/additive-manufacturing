import numpy as np
import torch

from pint import Quantity
from typing import cast

from am.solver.types import BuildConfig, MaterialConfig
from am.solver.mesh import SolverMesh
from am.segmenter.types import Segment

FLOOR = 10**-7  # Float32


class Rosenthal:
    def __init__(
        self,
        build_config: BuildConfig,
        material_config: MaterialConfig,
        solver_mesh: SolverMesh,
        device: str = "cpu",
        **kwargs,
    ):
        self.build_config: BuildConfig = build_config
        self.material_config: MaterialConfig = material_config
        self.device: str = device
        self.dtype = torch.float32
        self.num: int | None = kwargs.get("num", None)

        # Material Properties
        # Converted into SI units before passing to solver.
        self.absorptivity: Quantity = cast(
            Quantity, self.material_config.absorptivity.to("dimensionless")
        )
        self.thermal_diffusivity: Quantity = cast(
            Quantity, self.material_config.thermal_diffusivity.to("meter ** 2 / second")
        )
        self.thermal_conductivity: Quantity = cast(
            Quantity, self.material_config.thermal_conductivity.to("watts / (meter * kelvin)")
        )

        # Build Parameters
        self.beam_power: Quantity = cast(
            Quantity, self.build_config.beam_power.to("watts")
        )
        self.scan_velocity: Quantity = cast(
            Quantity, self.build_config.scan_velocity.to("meter / second")
        )
        self.temperature_preheat: Quantity = cast(
            Quantity, self.build_config.temperature_preheat.to("kelvin")
        )

        # Mesh Range
        self.X, self.Y, self.Z = torch.meshgrid(
            solver_mesh.x_range_centered,
            solver_mesh.y_range_centered,
            solver_mesh.z_range_centered,
            indexing="ij"
        )

        self.theta_shape: tuple[int, int, int] = (
            len(solver_mesh.x_range_centered),
            len(solver_mesh.y_range_centered),
            len(solver_mesh.z_range_centered),
        )

    def forward(self, segment: Segment) -> torch.Tensor:
        """
        Provides Eagar-Tsai approximation of the melt pool centered and rotated
        within the middle of the middle of the mesh.
        """

        phi = cast(float, segment.angle_xy.to("radian").magnitude)
        distance_xy = cast(float, segment.distance_xy.to("meter").magnitude)

        alpha = cast(float, self.absorptivity.magnitude)
        D = cast(float, self.thermal_diffusivity.magnitude)
        k = cast(float, self.thermal_conductivity.magnitude)
        pi = np.pi

        p = cast(float, self.beam_power.magnitude)
        if segment.travel:
            # Turn power off when travel
            p = 0.0

        v = cast(float, self.scan_velocity.magnitude)
        t_0 = cast(float, self.temperature_preheat.magnitude)

        # Coefficient for Equation 16 in Wolfer et al.
        # Temperature Flux
        # Kelvin * meter / second
        c = cast(float, alpha * p / (2 * pi * k))

        dt = distance_xy / v

        num = self.num
        if num is None:
            num = max(1, int(dt // 1e-4))

        theta = torch.ones(self.theta_shape, device=self.device, dtype=self.dtype) * t_0


        if dt > 0:
            for tau in torch.linspace(0, dt, steps=num, device=self.device):
                result = self.solve(tau, phi, D, v, c)
                theta += result

        return theta

    def solve(
        self,
        tau: torch.Tensor,
        phi: float,
        D: float,
        v: float,
        c: float,
    ) -> torch.Tensor:
        # Adds in the expected distance traveled along global x and y axes.
        x_travel = -v * tau * np.cos(phi)
        y_travel = -v * tau * np.sin(phi)

        # Assuming x is along the weld center line
        zeta = -(self.X - x_travel)

        # r is the cylindrical radius composed of y and z
        r = torch.sqrt((self.Y - y_travel) ** 2 + self.Z**2)

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
        temp = (c / R) * torch.exp((v * (zeta_rot - R)) / (2 * D))

        ########################
        # Temperature Clamping #
        ########################
        # TODO #1: Revisit this and see if there's a better solution.
        # Current implementation of rosenthal's equation seems to result in
        # temperatures much higher than melting and results in extreme
        # amounts of heat build up.

        # Prevents showing temperatures above liquidus
        # temp = torch.minimum(temp, torch.tensor(t_l))

        # Mask temperatures close to background to prevent "long tail"
        # temp[temp < t_s] = 0

        return temp

    def __call__(self, segment: Segment) -> torch.Tensor:
        return self.forward(segment)
