import math

from am import data
from importlib.resources import files
from pygcode import Line, words2dict, GCodeLinearMove
from tqdm import tqdm

# Names of parts included in package.
PARTS = ["overhang"]

class SegmenterGCode:
    """
    GCode parsing methods for Segmenter class.
    """

    def __init__(self):
        self.gcode_commands = []
        self.gcode_layer_change_indexes = []

    def load_gcode_commands(self, gcode_filepath):
        """
        Load and parse linear move values within GCode file.

        @param gcode_filepath: Absolute path for gcode file location.
        @return: List gcode command objects coordinate and action values.
        [
            {"x": 0.0, "y": 0.0, "z": 0.0, "e": 0.0},
            {"x": 0.1, "y": 0.1, "z": 0.0, "e": 2.1},
            {"x": 0.1, "y": 0.1, "z": 0.5, "e": 0.0},
            ...
        ],
        """
        self.gcode_layer_numbers = []
        self.gcode_commands = []  # Resets stored gcode command
        current_command = {
            "X": 0.0,
            "Y": 0.0,
            "Z": 0.0,
            "E": 0.0,
        }

        if gcode_filepath in PARTS:
            gcode_filepath = files(data).joinpath("segmenter", "part", f"{gcode_filepath}.gcode")

        with open(gcode_filepath, "r") as f:

            # Open gcode file to begin parsing linear moves line by line.
            for line_text in tqdm(f.readlines()):

                line = Line(line_text)  # Parses raw gcode text to line instance.

                gcodes = line.block.gcodes  # GCode objects within line text.

                if self.verbose:
                    print(gcodes)

                # Only considers Linear Move GCode actions for now.
                if len(gcodes) and isinstance(gcodes[0], GCodeLinearMove):

                    # Retrieves the coordinate values of the linear move.
                    # `{"Z": 5.0}` or `{"X": 1.0, "Y": 1.0}` or `{}`
                    # Sometimes `{"X": 1.0, "Y": 1.0, "Z": 5.0}` as well.
                    coordinates_dict = gcodes[0].get_param_dict()

                    # Indexes z coordinate commands as layer changes.
                    # Only count explicit Z layer changes (dict length of 1).
                    if len(coordinates_dict) == 1 and "Z" in coordinates_dict:
                        command_index = len(self.gcode_commands)
                        self.gcode_layer_change_indexes.append(command_index)

                    # Retrieves the corresponding extrusion value
                    # `{"E": 2.10293}` or `{}` if no extrusion.
                    extrusion_dict = words2dict(line.block.modal_params)

                    # Updates extrusion value explicity to 0.0.
                    if "E" not in extrusion_dict:
                        extrusion_dict = {"E": 0.0}

                    # Overwrites the current command with commands gcode line.
                    current_command = {
                        **current_command,
                        **coordinates_dict,
                        **extrusion_dict,
                    }

                    self.gcode_commands.append(current_command)

        return self.gcode_commands

    def get_gcode_commands_by_layer_change_index(self, layer_index):
        """
        Provides a list of gcode commands associated with a specific layer.
        """
        end_index = min(layer_index + 1, len(self.gcode_layer_change_indexes))

        # Start and stop indexes for gcode commands.
        command_start_index = self.gcode_layer_change_indexes[layer_index]
        command_end_index = self.gcode_layer_change_indexes[end_index]
        return self.gcode_commands[command_start_index:command_end_index]

    # TODO: Call these subsegments.
    def convert_gcode_commands_to_segments(
            self,
            gcode_commands = None,
            max_distance_xy = 1.0, # units are relative to GCode file.

            # TODO: Move this to be a more classwide setting.
            units = "mm",
        ):
        """
        Parses list of gcode commands to segments of x, y, z, and e since
        plotting all will unintentionally show travel movements.

        @param gcode_commands: List of gcode commands
        """
        if gcode_commands is None:
            gcode_commands = self.gcode_commands

        segments = []

        # Range of gcode commands allowing for indexing of next command.
        gcode_commands_range = range(len(gcode_commands) - 2)

        for gcode_command_index in tqdm(gcode_commands_range):
            current_gcode_command = gcode_commands[gcode_command_index]
            next_gcode_command = gcode_commands[gcode_command_index + 1]

            # Calculates lateral distance between two points.
            distance_xy = math.sqrt(
                (next_gcode_command["X"] - current_gcode_command["X"]) ** 2
                + (next_gcode_command["Y"] - current_gcode_command["Y"]) ** 2
            )

            quotient, remainder = divmod(distance_xy, max_distance_xy)
            num_segments = int(quotient)

            segment_distances = [max_distance_xy] * num_segments

            # Adds one more segment to account for remainder.
            if remainder > 0:
                num_segments += 1
                segment_distances.append(remainder)

            prev_x = current_gcode_command["X"]
            prev_y = current_gcode_command["Y"]
            prev_z = current_gcode_command["Z"]
            prev_e = current_gcode_command["E"]

            # Determines angle to reach given is translated to origin.
            translated_x = next_gcode_command["X"] - current_gcode_command["X"]
            translated_y = next_gcode_command["Y"] - current_gcode_command["Y"]
            prev_angle_xy = math.atan2(translated_y, translated_x)

            travel = False
            if next_gcode_command["E"] <= 0.0:
                travel = True

            # Handle no distance cases.
            if len(segment_distances) == 0:
                segment_distances = [0.0]

            for segment_index, segment_distance in enumerate(segment_distances):

                next_x = prev_x + segment_distance * math.cos(prev_angle_xy)
                next_y = prev_y + segment_distance * math.sin(prev_angle_xy)

                # Determines angle to reach given is translated to origin.
                translated_x = next_x - prev_x
                translated_y = next_y - prev_y
                next_angle_xy = math.atan2(translated_y, translated_x)

                # Assumes that these values do not change within subsegment.
                next_z = current_gcode_command["Z"]

                # TODO: This may be total extrusion rather than extrusion rate.
                # Thus may need to be divided as well.
                next_e = current_gcode_command["E"]

                if segment_index == len(segment_distances) - 1:
                    next_z = next_gcode_command["Z"]
                    next_e = next_gcode_command["E"]

                segment = {
                    "X": [prev_x, next_x],
                    "Y": [prev_y, next_y],
                    "Z": [prev_z, next_z],
                    "E": [prev_e, next_e],
                    "angle_xy": next_angle_xy,
                    "distance_xy": segment_distance,
                    "travel": travel,
                }

                if units == "mm":
                    segment = {
                        "X": [prev_x / 1000, next_x / 1000],
                        "Y": [prev_y / 1000, next_y / 1000],
                        "Z": [prev_z / 1000, next_z / 1000],
                        "E": [prev_e / 1000, next_e / 1000],
                        "angle_xy": next_angle_xy,
                        "distance_xy": segment_distance / 1000,
                        "travel": travel,
                    }

                segments.append(segment)

                prev_x = next_x
                prev_y = next_y
                prev_angle_xy = next_angle_xy

        return segments

    def convert_gcode_commands_to_segments_old(self, gcode_commands):
        """
        Parses list of gcode commands to segments of x, y, z, and e since
        plotting all will unintentionally show travel movements.

        @param gcode_commands: List of gcode commands
        """
        segments = []

        # Range of gcode commands allowing for indexing of next command.
        gcode_commands_range = range(len(gcode_commands) - 2)

        for gcode_command_index in tqdm(gcode_commands_range):
            current_gcode_command = gcode_commands[gcode_command_index]
            next_gcode_command = gcode_commands[gcode_command_index + 1]

            segment = {
                "X": [],
                "Y": [],
                "Z": [],
                "E": [],
                "angle_xy": 0.0,
                "distance_xy": 0.0,
                "travel": False,
            }

            # Adds start of segment
            for key, value in current_gcode_command.items():
                segment[key].append(value)

            # Adds end of segment
            for key, value in next_gcode_command.items():
                segment[key].append(value)

                # Marks segments with next gcode command without extrude values
                # as travel movements.
                if key == "E" and value <= 0.0:
                    segment["travel"] = True

            # Calculates lateral distance between two points.
            segment["distance_xy"] = math.sqrt(
                (segment["X"][1] - segment["X"][0]) ** 2
                + (segment["Y"][1] - segment["Y"][0]) ** 2
            )

            # Determines angle to reach given is translated to origin.
            translated_x = segment["X"][1] - segment["X"][0]
            translated_y = segment["Y"][1] - segment["Y"][0]
            segment["angle_xy"] = math.atan2(translated_y, translated_x)

            segments.append(segment)

        return segments