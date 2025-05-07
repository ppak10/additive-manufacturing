import gzip
import os
import torch
import numpy as np

from tqdm import tqdm


class SimulationBase:
    """
    Base file for Simulation class.
    """

    def __init__(
        self,
        segmenter=None,
        segmenter_path=None,
        solver=None,
        solver_path=None,
        name=None,
        filename=None,
        zfill=8,
        verbose=False,
        **kwargs,
    ):
        self.set_name(name, filename, segmenter, segmenter_path, solver, solver_path)

        # Directly loads segmenter and solver instance if provided as arguments.
        self.segmenter = segmenter
        self.solver = solver

        # Keeps path for segmenter and solver for loading later.
        # Load segmenter or solver with `self.load_segmenter()` or
        # `self.load_solver()` respectively.
        # Implemented for cases where loading torch in multiprocessing is not
        # ideal or necessary (i.e. visualization).
        self.segmenter_path = segmenter_path
        self.solver_path = solver_path

        self.zfill = zfill
        self.verbose = verbose
        super().__init__(**kwargs)

    def run_layer_index(self, layer_index, out_dir="segments", **kwargs):
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        # Load in layer segments from segmenter.
        gcode_layer_commands = self.segmenter.get_gcode_commands_by_layer_change_index(
            layer_index
        )
        gcode_segments = self.segmenter.convert_gcode_commands_to_segments(
            gcode_layer_commands, max_distance_xy=0.5
        )

        # Load initial coordinates into solver.
        self.solver.x = gcode_segments[0]["X"][0]
        self.solver.y = gcode_segments[0]["Y"][0]

        power = self.solver.power

        # TODO: Implement timesteps saving correctly since this is really just
        # gcode segments.
        for index in tqdm(range(len(gcode_segments))):

            segment = gcode_segments[index]
            dt = segment["distance_xy"] / self.solver.velocity

            if segment["travel"]:
                self.solver.power = 0

            else:
                self.solver.power = power

            # Torch
            # if dt > 0:
            #     self.solver.forward(segment)
            #     # TODO: Implement alternative saving functionalities that don't
            #     # write to disk as often.
            #     temperatures = self.solver.temperatures.cpu()
            #     filename = f"{index}".zfill(self.zfill)
            #     if save_compressed:
            #         file_path = os.path.join(out_dir, f"{filename}.pt.gz")
            #         with gzip.open(file_path, "wb") as f:
            #             torch.save(temperatures, f)
            #     else:
            #         file_path = os.path.join(out_dir, f"{filename}.pt")
            #         torch.save(temperatures, file_path)

            if dt > 0:
                self.solver.forward(segment)
                # TODO: Implement alternative saving functionalities that don't
                # write to disk as often.
                temperatures = self.solver.temperatures.cpu().numpy()
                filename = f"{index}".zfill(self.zfill)

                file_path = os.path.join(out_dir, f"{filename}.npz")
                np.savez(file_path, temperatures=temperatures)
