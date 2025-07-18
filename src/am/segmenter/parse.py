import numpy as np
import json

from pathlib import Path
from pygcode import Line, words2dict, GCodeLinearMove, GCode
from pint import Quantity
from typing import cast
from tqdm import tqdm

from .config import SegmenterConfig
from .types import Command, Segment, SegmentDict

class SegmenterParse:
    """
    Parses files (`.gcode`) into commands and then into segments.
    """

    def __init__(self, config: SegmenterConfig):
        self.config: SegmenterConfig = config
        self.commands: list[Command] = []
        self.segments: list[Segment] = []

        # List of indexes for `self.gcode_commands` where layer change occurs.
        self.commands_layer_change_indexes: list[int] = []
    
    def gcode_to_commands(self, path: Path, unit: str | None = None, verbose: bool | None = False):
        """
        Load and parse linear move values within GCode file into commands.

        @param path: Absolute path for gcode file location.
        @return: List gcode command objects coordinate and action values.
        [
            {
                'x': <Quantity(9.165, 'millimeter')>,
                'y': <Quantity(7.202, 'millimeter')>,
                'z': <Quantity(5.01, 'millimeter')>,
                'e': <Quantity(-1.43211, 'millimeter')>
            },
            ...
        ],
        """
        
        ureg = self.config.ureg

        # Parse the unit string using the registry if provided
        if unit is None:
            if ureg.default_system == "mks":
                unit = "m"
            if ureg.default_system == "cgs":
                unit = "cm"
            else:
                raise Exception("Unsupported ureg.default_system")

        _unit = ureg.parse_units(unit)

        # Initial starting command that gets mutated.
        current_command: Command  = {
            "x": 0.0 * _unit,
            "y": 0.0 * _unit,
            "z": 0.0 * _unit,
            "e": 0.0 * _unit,
        }

        # Clears command list
        self.commands = []

        with open(path, "r") as f:

            # Open gcode file to begin parsing linear moves line by line.
            for line_text in tqdm(f.readlines(), desc=f"Parsing GCode file", disable=not verbose):
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
                        # TODO: Make type stub for `.get_param_dict()` pygcode or fork package.
                        coordinates_dict = cast(dict[str, float], gcodes[0].get_param_dict())

                        # Indexes z coordinate commands as layer changes.
                        # Only count explicit Z layer changes (dict length of 1).
                        if len(coordinates_dict) == 1 and "Z" in coordinates_dict:
                            command_index = len(self.commands)
                            self.commands_layer_change_indexes.append(command_index)

                        # Retrieves the corresponding extrusion value
                        # `{"E": 2.10293}` or `{}` if no extrusion.
                        modal_params = cast(object, block.modal_params)

                        extrusion_dict = cast(dict[str, float], words2dict(modal_params))

                        # Updates extrusion value explicity to 0.0.
                        if "E" not in extrusion_dict:
                            extrusion_dict: dict[str, float] = { "E": 0.0 }

                        # Overwrites the current command with commands gcode line.
                        # Update with coordinates_dict values if present
                        for k in ["x", "y", "z"]:
                            if k.capitalize() in coordinates_dict:
                                current_command[k] = coordinates_dict[k.capitalize()] * _unit
                        
                        # Update extrusion 'E'
                        if "E" in extrusion_dict:
                            current_command["e"] = extrusion_dict["E"] * _unit

                        # .copy() is necessary otherwise current_command is all the same
                        self.commands.append(current_command.copy())

        return self.commands

    def commands_to_segments(
            self,
            commands: list[Command] | None = None,
            max_segment_length: float = 1.0,
            verbose: bool | None = False,
        ):
        """
        Converts commands to segments
        """
        ureg = self.config.ureg

        if commands is None:
            commands = self.commands
        
        self.segments = []

        # Range of gcode commands allowing for indexing of next command.
        commands_range = range(len(commands) - 2)

        # max_segment_length_quantity = max_segment_length

        for command_index in tqdm(commands_range, desc="Converting to segments", disable=not verbose):
            current_command = commands[command_index]
            next_command = commands[command_index + 1]

            # Calculates lateral distance between two points.
            dx = next_command["x"] - current_command["x"]
            dy = next_command["y"] - current_command["y"]
            dxdy = cast(Quantity, dx**2 + dy**2)
            distance_xy = dxdy ** 0.5

            units = distance_xy.units
            max_segment_length_quantity = ureg.Quantity(max_segment_length, units)

            # Divides `distance_xy` into segments split by `max_segment_length`
            quotient, remainder = divmod(distance_xy, max_segment_length_quantity)
            num_segments = int(quotient)
            segment_distances = [max_segment_length_quantity] * num_segments

            # Adds one more segment to account for remainder.
            if remainder > 0:
                num_segments += 1
                segment_distances.append(remainder)

            # Sets current command to previous command
            prev_x: Quantity = current_command["x"]
            prev_y: Quantity = current_command["y"]
            prev_z: Quantity = current_command["z"]
            prev_e: Quantity = current_command["e"]

            # Determines angle to reach given is translated to origin.
            translated_x = next_command["x"] - current_command["x"]
            translated_y = next_command["y"] - current_command["y"]
            prev_angle_xy = np.arctan2(translated_y, translated_x)

            travel = False
            if next_command["e"] <= 0.0:
                travel = True

            # Handle no distance cases.
            if len(segment_distances) == 0:
                segment_distances = [ureg.Quantity(0.0, units)]

            for segment_index, segment_distance in enumerate(segment_distances):

                next_x = cast(Quantity, prev_x + segment_distance * np.cos(prev_angle_xy))
                next_y = cast(Quantity, prev_y + segment_distance * np.sin(prev_angle_xy))

                # Determines angle to reach given is translated to origin.
                translated_x = next_x - prev_x
                translated_y = next_y - prev_y
                next_angle_xy = np.arctan2(translated_y, translated_x)

                # Assumes that these values do not change within subsegment.
                next_z = current_command["z"]

                # TODO: This may be total extrusion rather than extrusion rate.
                # Thus may need to be divided as well.
                next_e = current_command["e"]

                if segment_index == len(segment_distances) - 1:
                    next_z = next_command["z"]
                    next_e = next_command["e"]

                segment = Segment(
                    x=prev_x,
                    y=prev_y,
                    z=prev_z,
                    e=prev_e,
                    x_next=next_x,
                    y_next=next_y,
                    z_next=next_z,
                    e_next=next_e,

                    # TODO: Investigate a better way to assign type here.
                    angle_xy=cast(Quantity, cast(object, next_angle_xy)),
                    distance_xy=cast(Quantity, segment_distance),
                    travel=travel,
                )

                self.segments.append(segment)

                prev_x = next_x
                prev_y = next_y
                prev_angle_xy = next_angle_xy

        return self.segments

    def save_segments(
            self,
            path: Path | str,
            segments: list[Segment] | None = None,
            verbose: bool | None = False
        ) -> Path:

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if segments is None:
            segments = self.segments

        segments_data = [
            segment.to_dict() for segment in tqdm(segments, desc="Serializing segments", disable=not verbose)
        ]

        # with path.open("w") as f:
        #     json.dump(segments_data, f, indent=2)

        with path.open("w") as f:
            _ = f.write("[\n")
            for i, segment_dict in enumerate(tqdm(segments_data, desc="Writing segments", disable=not verbose)):
                json_str = json.dumps(segment_dict, indent=2)
                indented_str = "  " + json_str.replace("\n", "\n ")  # 2-space indent after [
                _ = f.write(indented_str)
                if i < len(segments_data) - 1:
                    _ = f.write(",\n")
                else:
                    _ = f.write("\n")
            _ = f.write("]\n")

        return path

    def load_segments(self, path: Path | str) -> list[Segment]:
        path = Path(path)
        with path.open("r") as f:
            segments_data = cast(list[SegmentDict], json.load(f))

        self.segments = [Segment.from_dict(seg_dict) for seg_dict in segments_data]
        return self.segments

