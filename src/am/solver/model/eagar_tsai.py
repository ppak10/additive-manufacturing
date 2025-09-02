import numpy as np
import torch

from pint import Quantity
from scipy import integrate
from typing import cast

from am.schema import BuildParameters, Material
from am.solver.mesh import SolverMesh
from am.segmenter.types import Segment

FLOOR = 10**-7  # Float32


class EagarTsai:
    def __init__(
        self,
        build_parameters: BuildParameters,
        material: Material,
        solver_mesh: SolverMesh,
        device: str = "cpu",
        **kwargs,
    ):
        self.build_parameters: BuildParameters = build_parameters
        self.material: Material = material
        self.device: str = device
        self.dtype = torch.float32
        self.num: int | None = kwargs.get("num", None)

        # Material Properties
        # Converted into SI units before passing to solver.
        self.absorptivity = cast(Quantity, self.material.absorptivity).to(
            "dimensionless"
        )
        self.specific_heat_capacity = cast(
            Quantity, self.material.specific_heat_capacity
        ).to("joule / (kelvin * kilogram)")
        self.thermal_diffusivity = cast(Quantity, self.material.thermal_diffusivity).to(
            "meter ** 2 / second"
        )
        self.density = cast(Quantity, self.material.density).to("kilogram / meter ** 3")

        # Build Parameters
        self.beam_diameter = (
            cast(Quantity, self.build_parameters.beam_diameter).to("meter") / 4
        )
        self.beam_power = cast(Quantity, self.build_parameters.beam_power).to("watts")
        self.scan_velocity = cast(Quantity, self.build_parameters.scan_velocity).to(
            "meter / second"
        )
        self.temperature_preheat = cast(
            Quantity, self.build_parameters.temperature_preheat
        ).to("kelvin")

        # Mesh Range
        self.X: torch.Tensor = solver_mesh.x_range_centered[:, None, None, None]
        self.Y: torch.Tensor = solver_mesh.y_range_centered[None, :, None, None]
        self.Z: torch.Tensor = solver_mesh.z_range_centered[None, None, :, None]

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
        c_p = cast(float, self.specific_heat_capacity.magnitude)
        D = cast(float, self.thermal_diffusivity.magnitude)
        pi = np.pi
        rho = cast(float, self.density.magnitude)
        sigma = cast(float, self.beam_diameter.magnitude)

        p = cast(float, self.beam_power.magnitude)
        if segment.travel:
            # Turn power off when travel
            p = 0.0

        v = cast(float, self.scan_velocity.magnitude)

        t_0 = cast(float, self.temperature_preheat.magnitude)

        # Coefficient for Equation 16 in Wolfer et al.
        # Temperature Flux
        # Kelvin * meter / second
        c = cast(float, alpha * p / (2 * pi * sigma**2 * rho * c_p * pi ** (3 / 2)))

        dt = distance_xy / v

        theta = torch.ones(self.theta_shape, device=self.device, dtype=self.dtype) * t_0

        num = self.num
        if num is None:
            num = max(1, int(dt // 1e-4))

        if dt > 0:
            result, _ = integrate.fixed_quad(
                self.solve, FLOOR, dt, args=(phi, D, sigma, v, c), n=num
            )
            result_tensor = torch.tensor(result)
            theta += result_tensor

        return theta

    def solve(
        self,
        tau: np.ndarray,
        phi: float,
        D: float,
        sigma: float,
        v: float,
        c: float,
    ) -> np.ndarray:
        """
        Free Template Solution
        """
        x_travel = -v * tau * np.cos(phi)
        y_travel = -v * tau * np.sin(phi)

        lmbda = np.sqrt(4 * D * tau)
        gamma = np.sqrt(2 * sigma**2 + lmbda**2)
        start = (4 * D * tau) ** (-3 / 2)

        # Wolfer et al. Equation A.3
        termy = sigma * lmbda * np.sqrt(2 * np.pi) / (gamma)
        yexp1 = np.exp(-1 * ((self.Y.cpu().numpy() - y_travel) ** 2) / (gamma**2))
        yintegral = termy * yexp1

        # Wolfer et al. Equation A.2
        termx = termy
        xexp1 = np.exp(-1 * ((self.X.cpu().numpy() - x_travel) ** 2) / (gamma**2))
        xintegral = termx * xexp1

        # Wolfer et al. Equation 18
        zintegral = 2 * np.exp(-(self.Z.cpu().numpy() ** 2) / (4 * D * tau))

        # Wolfer et al. Equation 16
        result = c * start * yintegral * xintegral * zintegral
        return result

    def __call__(self, segment: Segment) -> torch.Tensor:
        return self.forward(segment)
