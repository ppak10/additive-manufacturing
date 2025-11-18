import numpy as np
import jax.numpy as jnp

from jax import Array
from pint import Quantity
from typing import cast

from am.config import BuildParameters, Material
from am.solver.types import MeltPoolDimensions
from am.solver.mesh import SolverMesh
from am.solver.segment import SolverSegment

FLOOR = 10**-7  # Float32


class Rosenthal:
    def __init__(
        self,
        build_parameters: BuildParameters,
        material: Material,
        solver_mesh: SolverMesh | None = None,
        **kwargs,
    ):
        self.build_parameters: BuildParameters = build_parameters
        self.material: Material = material
        self.dtype = jnp.float32
        self.num: int | None = kwargs.get("num", None)

        # Material Properties
        # Converted into SI units before passing to solver.
        self.absorptivity = cast(Quantity, self.material.absorptivity).to(
            "dimensionless"
        )
        self.thermal_diffusivity = self.material.thermal_diffusivity.to(
            "meter ** 2 / second"
        )
        self.thermal_conductivity = cast(
            Quantity, self.material.thermal_conductivity
        ).to("watts / (meter * kelvin)")
        self.temperature_melt = cast(Quantity, self.material.temperature_melt).to(
            "kelvin"
        )

        # Build Parameters
        self.beam_power = cast(Quantity, self.build_parameters.beam_power).to("watts")
        self.scan_velocity = cast(Quantity, self.build_parameters.scan_velocity).to(
            "meter / second"
        )
        self.temperature_preheat = cast(
            Quantity, self.build_parameters.temperature_preheat
        ).to("kelvin")

        # Mesh Range
        self.solver_mesh = solver_mesh
        if solver_mesh is not None:
            self.X, self.Y, self.Z = jnp.meshgrid(
                solver_mesh.x_range_centered,
                solver_mesh.y_range_centered,
                solver_mesh.z_range_centered,
                indexing="ij",
            )

            self.theta_shape: tuple[int, int, int] = (
                len(solver_mesh.x_range_centered),
                len(solver_mesh.y_range_centered),
                len(solver_mesh.z_range_centered),
            )

    def forward(self, segment: SolverSegment) -> Array:
        """
        Provides Eagar-Tsai approximation of the melt pool centered and rotated
        within the middle of the middle of the mesh.
        """

        if self.solver_mesh is None:
            raise Exception("self.solver_mesh is not defined,")

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

        theta = jnp.ones(self.theta_shape, dtype=self.dtype) * t_0

        if dt > 0:
            for tau in jnp.linspace(0, dt, num):
                result = self.solve(tau, phi, D, v, c)
                theta += result

        return theta

    def solve_melt_pool_dimensions(self) -> MeltPoolDimensions:
        alpha = self.absorptivity.magnitude
        p = self.beam_power.magnitude
        k = self.thermal_conductivity.magnitude
        D = self.thermal_diffusivity.magnitude
        t_melt = self.temperature_melt.magnitude
        t_0 = self.temperature_preheat.magnitude
        t_delta = t_melt - t_0
        v = self.scan_velocity.magnitude

        R_tail = (alpha * p) / (2 * np.pi * k * t_delta)

        # Generate R values up to slightly beyond the tail
        R_values = np.linspace(1e-6, R_tail * 1.1, 5000)

        max_width_r = 0
        min_z = 0  # Length in front of heat source (negative z)
        width_point_z = 0

        def rosenthal(R):
            return R + (
                ((2 * D) / v) * np.log((2 * np.pi * k * R * t_delta) / (alpha * p))
            )

        for R in R_values:
            # Rosenthal equation: z = f(R)
            z = rosenthal(R)

            if R**2 > z**2:
                r = np.sqrt(R**2 - z**2)

                # Track maximum r (width point where dr/dz ≈ 0)
                if r > max_width_r:
                    max_width_r = r
                    # width_point_z = z

                # Track minimum z (length in front of heat source)
                if z < min_z:
                    min_z = z

        # Maximum z occurs at the tail point (length behind heat source)
        max_z = rosenthal(R_tail)

        depth = Quantity(max_width_r, "m").to("micron")
        width = Quantity(2 * max_width_r, "m").to("micron")
        length = Quantity(max_z - min_z, "m").to("micron")
        length_front = Quantity(abs(min_z), "m").to("micron")
        length_behind = Quantity(max_z, "m").to("micron")

        melt_pool_dimensions = MeltPoolDimensions(
            depth=cast(Quantity, depth),
            width=cast(Quantity, width),
            length=cast(Quantity, length),
            length_front=cast(Quantity, length_front),
            length_behind=cast(Quantity, length_behind),
        )

        return melt_pool_dimensions

    def solve(
        self,
        tau: Array,
        phi: float,
        D: float,
        v: float,
        c: float,
    ) -> Array:
        # Adds in the expected distance traveled along global x and y axes.
        x_travel = -v * tau * np.cos(phi)
        y_travel = -v * tau * np.sin(phi)

        # Assuming x is along the weld center line
        zeta = -(self.X - x_travel)

        # r is the cylindrical radius composed of y and z
        r = jnp.sqrt((self.Y - y_travel) ** 2 + self.Z**2)

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
        min_R = jnp.array(FLOOR)

        R = jnp.maximum(jnp.sqrt(zeta_rot**2 + r_rot**2), min_R)

        # Rosenthal temperature contribution
        # `notes/rosenthal/#shape_of_temperature_field`
        temp = (c / R) * jnp.exp((v * (zeta_rot - R)) / (2 * D))

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

    def __call__(self, segment: SolverSegment) -> Array:
        return self.forward(segment)
