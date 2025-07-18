import torch

from am.units import MMGS


class SolverBase:
    """
    Base file for Solver class.
    """

    def __init__(
        self,
        model,
        name=None,
        filename=None,
        build_config_file="default.ini",
        material_config_file="SS316L.ini",
        mesh_config_file="scale_millimeter.ini",
        device="cpu",
        dtype=torch.float32,
        units=MMGS,
        verbose=False,
        # TODO: Add setting for dtype
        # This may help with reducing size and computational cost.
        **kwargs,
    ):
        self.set_name(name, filename, model)
        self.device = device
        self.dtype = dtype
        self.units = units
        self.verbose = verbose
        self.model = model

        ################
        # Config Files #
        ################
        self.load_config_file("build", build_config_file)
        self.load_config_file("material", material_config_file)
        self.load_config_file("mesh", mesh_config_file)

        # Sets override values to that provided in kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

        ######################
        # Computed Constants #
        ######################

        # Thermal Diffusivity (Wolfer et al. Equation 1)
        self.thermal_diffusivity = self.thermal_conductivity / (
            self.density * self.specific_heat_capacity
        )

        ########
        # Mesh #
        ########

        # Determine bounds for mesh
        self.x_start = self.x_min - self.x_start_pad
        self.x_end = self.x_max + self.x_end_pad
        self.y_start = self.y_min - self.y_start_pad
        self.y_end = self.y_max + self.y_end_pad
        self.z_start = self.z_min - self.z_start_pad
        self.z_end = self.z_max + self.z_end_pad

        # Create mesh for x, y, and z dimensions with prescribed step size
        self.X = torch.arange(
            self.x_start, self.x_end, self.x_step, device=self.device, dtype=self.dtype
        )
        self.Y = torch.arange(
            self.y_start, self.y_end, self.y_step, device=self.device, dtype=self.dtype
        )
        self.Z = torch.arange(
            self.z_start, self.z_end, self.z_step, device=self.device, dtype=self.dtype
        )

        # Centered x, y, and z coordinates for use in solver models
        self.X_c = self.X - self.X[len(self.X) // 2]
        self.Y_c = self.Y - self.Y[len(self.Y) // 2]
        self.Z_c = self.Z

        #########
        # State #
        #########

        # Initial and current locations for x, y, z within the mesh
        self.x, self.y, self.z = self.x_initial, self.y_initial, self.z_initial

        # Index of x, y, and z locations within the mesh
        self.x_index = int(round((self.x_initial - self.x_start) / self.x_step))
        self.y_index = int(round((self.y_initial - self.y_start) / self.y_step))
        self.z_index = int(round((self.z_initial - self.z_start) / self.z_step))

        # Previously referred to by `self.thetas`.
        self.temperatures = torch.full(
            (len(self.X), len(self.Y), len(self.Z)),
            self.temperature_preheat,
            device=device,
            dtype=self.dtype,
        )

        super().__init__()

        print(self.__dict__)

    def forward(self, segment):

        dt = segment["distance_xy"] / self.velocity
        phi = segment["angle_xy"]

        match self.model:
            case "eagar-tsai":
                theta = self.eagar_tsai(dt, phi)
            case "rosenthal":
                theta = self.rosenthal(dt, phi)
            case "surrogate-ss316":
                theta = self.surrogate_ss316(dt, phi)
            case _:
                print(f"'{self.model}' model not found")

        self.temperatures = self.diffuse(dt)
        self.update_location(segment)
        self.temperatures = self.graft(theta)

    def update_location(self, segment, mode="absolute"):
        """
        Method to update location via command
        @param segment
        @param mode: "global" for next xy, or "relative" for distance and phi
        """
        match mode:
            case "absolute":
                # Updates using prescribed GCode positions in segment.
                # This limits potential drift caused by rounding to mesh indexes

                next_x, next_y = segment["X"][1], segment["Y"][1]

                next_x_index = round((next_x - self.x_start) / self.x_step)
                next_y_index = round((next_y - self.y_start) / self.y_step)

                self.x, self.y = next_x, next_y
                self.x_index, self.y_index = next_x_index, next_y_index

            case "relative":
                # Updates relative to `phi` and `dt` values
                # Can potentially drift results if
                # TODO: Implement
                dt = segment["distance_xy"] / self.build["velocity"]

    # TODO: Move to its own class and implement properly for edge and corner cases
    def graft(self, theta):
        x_offset, y_offset = len(self.X) // 2, len(self.Y) // 2

        # Calculate roll amounts
        x_roll = round(-x_offset + self.x_index)
        y_roll = round(-y_offset + self.y_index)

        # Update prev_theta using torch.roll and subtract background temperature
        roll = (
            torch.roll(theta, shifts=(x_roll, y_roll, 0), dims=(0, 1, 2))
            - self.temperature_preheat
        )
        return self.temperatures + roll
