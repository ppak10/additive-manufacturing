import gzip
import os
import torch

from datetime import datetime
from tqdm import tqdm

class SimulationBase:
    """
    Base file for Simulation class.
    """

    def __init__(self, name=None, filename=None, verbose = False, **kwargs):
        self.set_name(name, filename)

        self.verbose = verbose
        super().__init__(**kwargs)

    def set_name(self, name = None, filename = None):
        """
        Sets the `name` and `filename` values of the class.

        @param name: Name of simulation
        @param filename: `filename` override of simulation (no spaces)
        """
        # Sets `name` to approximate timestamp.
        if name is None:
            self.name = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.name = name

        # Autogenerates `filename` from `name` if not provided.
        if filename == None:
            self.filename = self.name.replace(" ", "_")
        else:
            self.filename = filename

    def run_layer_index(
            self,
            segmenter,
            solver,
            layer_index,
            out_dir="timesteps",
            save_compressed=False,
            **kwargs
        ):
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)

        # Load in layer segments from segmenter.
        gcode_layer_commands = segmenter.get_gcode_commands_by_layer_change_index(layer_index)
        gcode_segments = segmenter.convert_gcode_commands_to_segments(gcode_layer_commands, max_distance_xy=0.5)

        # Load initial coordinates into solver.
        solver.x = gcode_segments[0]["X"][0]
        solver.y = gcode_segments[0]["Y"][0]

        power = solver.power

        gcode_segments_length = len(gcode_segments)
        max_digits = len(str(abs(gcode_segments_length)))

        # TODO: Implement timesteps saving correctly since this is really just
        # gcode segments.
        for index in tqdm(range(len(gcode_segments))):
        
            segment = gcode_segments[index]
            dt = segment["distance_xy"] / solver.velocity

            if segment["travel"]:
                solver.power = 0

            else:
                solver.power = power

            if dt > 0:
                solver.forward(segment)
                # TODO: Implement alternative saving functionalities that don't
                # write to disk as often.
                temperatures = solver.temperatures.cpu()
                filename = f"{index}".zfill(max_digits)
                if save_compressed:
                    file_path = os.path.join(out_dir, f"{filename}.pt.gz")
                    with gzip.open(file_path, "wb") as f:
                        torch.save(temperatures, f)
                else:
                    file_path = os.path.join(out_dir, f"{filename}.pt")
                    torch.save(temperatures, file_path)
