import numpy as np
import torch

from pint import Quantity
from scipy import integrate
from typing import cast

from am.solver.types import BuildConfig, MaterialConfig
from am.solver.mesh import SolverMesh
from am.segmenter.types import Segment

FLOOR = 10**-7  # Float32

class EagarTsai:
    def __init__(
            self,
            build_config: BuildConfig,
            material_config: MaterialConfig,
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
            Quantity,
            self.material_config.absorptivity.to(
                "dimensionless"
            )
        )
        self.specific_heat_capacity: Quantity = cast(
            Quantity,
            self.material_config.specific_heat_capacity.to(
                "joule / (kelvin * kilogram)"
            )
        )
        self.thermal_diffusivity: Quantity = cast(
            Quantity,
            self.material_config.thermal_diffusivity.to(
                "meter ** 2 * watt / joule"
            )
        )
        self.density: Quantity = cast(
            Quantity,
            self.material_config.density.to(
                "kilogram / meter ** 3"
            )
        )

        # Build Parameters
        self.beam_diameter: Quantity = cast(
            Quantity,
            self.build_config.beam_diameter.to("meter") / 4
        )
        self.beam_power: Quantity = cast(
            Quantity,
            self.build_config.beam_power.to("watts")
        )
        self.scan_velocity: Quantity = cast(
            Quantity,
            self.build_config.scan_velocity.to("meter / second")
        )
        self.temperature_preheat: Quantity = cast(
            Quantity,
            self.build_config.temperature_preheat.to("kelvin")
        )

    def forward(self, solver_mesh: SolverMesh, segment: Segment) -> SolverMesh:
        """
        Provides next state for eagar tsai modeling
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
        v = cast(float, self.scan_velocity.magnitude)

        t_0 = cast(float, self.temperature_preheat.magnitude)

        # Coefficient for Equation 16 in Wolfer et al.
        # Temperature Flux
        # Kelvin * meter / second
        c = cast(float, alpha * p / (2 * pi * sigma**2 * rho * c_p * pi ** (3 / 2)))

        dt = distance_xy / v

        if segment.travel:
            # Turn power off when travel
            p = 0.0
    
        X = solver_mesh.x_range_centered[:, None, None, None]
        Y = solver_mesh.y_range_centered[None, :, None, None]
        Z = solver_mesh.z_range_centered[None, None, :, None]
    
        theta_shape = (
            len(solver_mesh.x_range_centered),
            len(solver_mesh.y_range_centered),
            len(solver_mesh.z_range_centered)
        )
    
        theta = torch.ones(
            theta_shape,
            device=self.device,
            dtype=self.dtype
        ) * t_0
    
    
        num = self.num
        if num is None:
            num = max(1, int(dt // 1e-4))
   
        if dt > 0:
            result, _ = integrate.fixed_quad(
                self.solve,
                FLOOR,
                dt,
                args=(phi, D, sigma, v, c, X, Y, Z),
                n=num
            )
            result_tensor = torch.tensor(result)
            solver_mesh.grid = theta + result_tensor
   
        return solver_mesh

    def solve(
            self,
            tau: np.ndarray,
            phi: float,
            D: float,
            sigma: float,
            v: float,
            c: float,
            X: torch.Tensor,
            Y: torch.Tensor,
            Z: torch.Tensor,
        ) -> np.ndarray:
        x_travel = cast(np.ndarray, -v * tau * np.cos(phi))
        y_travel = cast(np.ndarray, -v * tau * np.sin(phi))
    
        lmbda = (4 * D * tau) ** 0.5
        gamma = np.sqrt(2 * sigma**2 + lmbda**2)
        start = (4 * D * tau) ** (-3 / 2)
    
        termy = cast(np.ndarray, sigma * lmbda * np.sqrt(2 * np.pi) / (gamma ** 2))
        yexp1 = np.exp(-1 * ((Y.cpu() - y_travel) ** 2) / gamma**2)
        yintegral = termy * np.array(yexp1)
   
        termx = termy
        xexp1 = np.exp(-1 * ((X.cpu() - x_travel) ** 2) / gamma**2)
        xintegral = termx * np.array(xexp1)
    
        zintegral = np.array(2 * np.exp(-(Z.cpu() ** 2) / (4 * D * tau)))
    
        result = c * start * xintegral * yintegral * zintegral
        return result

    def __call__(self, solver_mesh: SolverMesh, segment: Segment) -> SolverMesh:
        return self.forward(solver_mesh, segment)

