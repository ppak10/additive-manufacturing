from pathlib import Path
from pygcode import Line, words2dict, GCodeLinearMove, GCode
from typing import cast, TypedDict
from tqdm import tqdm

from .config import SegmenterConfig

class Command(TypedDict, total=False):
    X: float
    Y: float
    Z: float
    E: float

class SegmenterGCode:
    """
    GCode parsing methods for segmenter class.
    """

    def __init__(self, config: SegmenterConfig):
        self.config: SegmenterConfig = config
        self.commands: list[Command] = []

        # List of indexes for `self.gcode_commands` where layer change occurs.
        self.commands_layer_change_indexes: list[int] = []
    
    def load(self, path: Path):
        """
        Load and parse linear move values within GCode file.

        @param path: Absolute path for gcode file location.
        @return: List gcode command objects coordinate and action values.
        [
            {"X": 0.0, "Y": 0.0, "Z": 0.0, "E": 0.0},
            {"X": 0.1, "Y": 0.1, "Z": 0.0, "E": 2.1},
            {"X": 0.1, "Y": 0.1, "Z": 0.5, "E": 0.0},
            ...
        ],
        """

        # Initial starting command that gets mutated.
        current_command: Command  = {
            "X": 0.0,
            "Y": 0.0,
            "Z": 0.0,
            "E": 0.0,
        }

        # Clears command list
        self.commands = []

        with open(path, "r") as f:

            # Open gcode file to begin parsing linear moves line by line.
            for line_text in tqdm(f.readlines()):
                line = Line(line_text)  # Parses raw gcode text to line instance.
                block = line.block

                if block is not None:
                    # GCode objects within line text.
                    gcodes = cast(list[GCode], block.gcodes)


                    # Only considers Linear Move GCode actions for now.
                    if len(gcodes) and isinstance(gcodes[0], GCodeLinearMove):

                        # Retrieves the coordinate values of the linear move.
                        # `{"Z": 5.0}` or `{"X": 1.0, "Y": 1.0}` or `{}`
                        # Sometimes `{"X": 1.0, "Y": 1.0, "Z": 5.0}` as well.
                        coordinates_dict: dict[str, float] = gcodes[0].get_param_dict()

                        # Indexes z coordinate commands as layer changes.
                        # Only count explicit Z layer changes (dict length of 1).
                        if len(coordinates_dict) == 1 and "Z" in coordinates_dict:
                            command_index = len(self.commands)
                            self.commands_layer_change_indexes.append(command_index)

                        # Retrieves the corresponding extrusion value
                        # `{"E": 2.10293}` or `{}` if no extrusion.
                        modal_params = cast(object, block.modal_params)
                        extrusion_dict: dict[str, float] = words2dict(modal_params)

                        # Updates extrusion value explicity to 0.0.
                        if "E" not in extrusion_dict:
                            extrusion_dict = {"E": 0.0}

                        # Overwrites the current command with commands gcode line.
                        # Update with coordinates_dict values if present
                        for k in ["X", "Y", "Z"]:
                            if k in coordinates_dict:
                                current_command[k] = coordinates_dict[k]
                        
                        # Update extrusion 'E'
                        if "E" in extrusion_dict:
                            current_command["E"] = extrusion_dict["E"]

                        self.commands.append(current_command)

        return self.commands

