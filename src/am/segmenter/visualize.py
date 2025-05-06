import os
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, PillowWriter
from tqdm import tqdm

def get_bounds(gcode_commands):
    # Range of gcode commands allowing for indexing of next command.
    gcode_commands_range = range(len(gcode_commands) - 2)

    min_x = None
    max_x = None
    min_y = None
    max_y = None

    for gcode_command_index in tqdm(gcode_commands_range):
        current_gcode_command = gcode_commands[gcode_command_index]
        next_gcode_command = gcode_commands[gcode_command_index + 1]

        x = current_gcode_command["X"]
        y = current_gcode_command["Y"]

        travel = False
        if next_gcode_command["E"] <= 0.0:
            travel = True
        
        if not travel:
            if min_x is None or x < min_x:
                min_x = x
            if min_y is None or y < min_y:
                min_y = y
            if max_x is None or x > max_x:
                max_x = x
            if max_y is None or y > max_y:
                max_y = y

    return min_x, min_y, max_x, max_y
        

class SegmenterVisualize:
    """
    Methods for visualizing segments.
    """

    def visualize_layer_index(self, layer_index, units = "mm"):
        """
        Creates `.gif` animation of layer within gcode file.
        """

        gcode_layer_commands = self.get_gcode_commands_by_layer_change_index(layer_index)
        gcode_segments = self.convert_gcode_commands_to_segments(gcode_layer_commands)


        if len(gcode_segments) < 1:
            print(f"layer_index: {0} has no gcode_segments.")
            return None

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        # TODO: Implement scale
        scale = 1000
        if units == "mm":
            scale = 1000

        # min_x = min(d['X'] for d in gcode_layer_commands)
        # max_x = max(d['X'] for d in gcode_layer_commands)
        # min_y = min(d['Y'] for d in gcode_layer_commands)
        # max_y = max(d['Y'] for d in gcode_layer_commands)

        min_x, min_y, max_x, max_y = get_bounds(gcode_layer_commands)

        print(f"Auto Bounds: ({min_x}, {min_y}), ({max_x}, {max_y})")

        # padding = 0.01 / scale
        ax.set_xlim(min_x / scale, max_x / scale)
        ax.set_ylim(min_y / scale, max_y / scale)

        def update(index):
        
            line = gcode_segments[index]

            if not line["travel"]:
                x = [line["X"][0], line["X"][1]]
                y = [line["Y"][0], line["Y"][1]]
                ax.plot(x, y)

        animate = FuncAnimation(fig, update, frames=tqdm(range(len(gcode_segments))))

        layer_string = f"{layer_index}".zfill(8)
        filename = f"{layer_string}.gif"
        path = os.path.join("segmenters", self.filename, "layers", filename)

        animate.save(path, writer=PillowWriter(fps=20))

