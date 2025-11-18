import numpy as np
import json

from mcp.server.fastmcp import Context
from pathlib import Path
from pygcode import Line, words2dict, GCodeLinearMove, GCode
from pint import Quantity, Unit
from typing import cast
from typing_extensions import TypedDict
from tqdm import tqdm

from am.solver.segment import SolverSegment


class Command(TypedDict):
    x: Quantity
    y: Quantity
    z: Quantity
    e: Quantity


class SegmenterParse:
    """
    Parses files (`.gcode`) into commands and then into segments.
    """

    def __init__(self):
        self.commands: list[Command] = []
        self.segments: list[SolverSegment] = []

        # List of indexes for `self.commands` where layer change occurs.
        self.commands_layer_change_indexes: list[int] = []
        self.segments_layer_change_indexes: list[int] = []

    async def gcode_to_commands(
        self,
        path: Path,
        unit: str = "mm",
        verbose: bool | None = False,
        context: Context | None = None,
    ):
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
        _unit = Unit(unit)

        # Initial starting command that gets mutated.
        current_command: Command = {
            "x": 0.0 * _unit,
            "y": 0.0 * _unit,
            "z": 0.0 * _unit,
            "e": 0.0 * _unit,
        }

        # Clears command list
        self.commands = []

        with open(path, "r") as f:

            lines = f.readlines()

        # Open gcode file to begin parsing linear moves line by line.
        for line_index, line_text in tqdm(
            enumerate(lines), desc=f"Parsing GCode file", disable=not verbose
        ):
            if context is not None:
                await context.report_progress(
                    progress=line_index + 1,
                    total=len(lines),
                    message=f"Parsing lines in GCode file {line_index + 1}/{len(lines)}",
                )

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
                    coordinates_dict = cast(
                        dict[str, float], gcodes[0].get_param_dict()
                    )

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
                        extrusion_dict: dict[str, float] = {"E": 0.0}

                    # Overwrites the current command with commands gcode line.
                    # Update with coordinates_dict values if present
                    for k in ["x", "y", "z"]:
                        if k.capitalize() in coordinates_dict:
                            current_command[k] = (
                                coordinates_dict[k.capitalize()] * _unit
                            )

                    # Update extrusion 'E'
                    if "E" in extrusion_dict:
                        current_command["e"] = extrusion_dict["E"] * _unit

                    # .copy() is necessary otherwise current_command is all the same
                    self.commands.append(current_command.copy())

        return self.commands

    async def commands_to_segments(
        self,
        commands: list[Command] | None = None,
        distance_xy_max: float = 1.0,
        units: str = "mm",
        verbose: bool | None = False,
        context: Context | None = None,
    ):
        """
        Converts commands to segments
        """

        if commands is None:
            commands = self.commands

        self.segments = []

        # Range of gcode commands allowing for indexing of next command.
        commands_range = range(len(commands) - 2)

        for command_index in tqdm(
            commands_range, desc="Converting to segments", disable=not verbose
        ):
            if context is not None:
                await context.report_progress(
                    progress=command_index + 1,
                    total=len(commands_range),
                    message=f"Converting commands to segments {command_index + 1}/{len(commands_range)}",
                )

            if command_index in self.commands_layer_change_indexes:
                # Adds current length of segments if command is marked as a
                # layer change.
                self.segments_layer_change_indexes.append(len(self.segments))

            current_command = commands[command_index]
            next_command = commands[command_index + 1]

            # Calculates lateral distance between two points.
            dx = next_command["x"] - current_command["x"]
            dy = next_command["y"] - current_command["y"]
            dxdy = cast(Quantity, dx**2 + dy**2)
            distance_xy = dxdy**0.5

            max_segment_length = cast(Quantity, Quantity(distance_xy_max, units))

            # Divides `distance_xy` into segments split by `max_segment_length`
            quotient, remainder = divmod(distance_xy, max_segment_length)
            num_segments = int(quotient)
            segment_distances = [max_segment_length] * num_segments

            # Adds one more segment to account for remainder.
            if remainder > 0:
                num_segments += 1
                segment_distances.append(cast(Quantity, remainder))

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
                segment_distances = [Quantity(0.0, units)]

            for segment_index, segment_distance in enumerate(segment_distances):

                next_x = cast(
                    Quantity, prev_x + segment_distance * np.cos(prev_angle_xy)
                )
                next_y = cast(
                    Quantity, prev_y + segment_distance * np.sin(prev_angle_xy)
                )

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

                segment = SolverSegment(
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
        path: Path,
        segments: list[SolverSegment] | None = None,
        verbose: bool | None = False,
        split_by_layer: bool | None = True,
    ) -> Path:

        path.parent.mkdir(parents=True, exist_ok=True)

        if segments is None:
            segments = self.segments

        segments_data = [
            segment.to_dict()
            for segment in tqdm(
                segments, desc="Serializing segments", disable=not verbose
            )
        ]

        if split_by_layer:
            # Saves start at 001.
            layer_changes = len(self.segments_layer_change_indexes)
            segments_name = path.with_suffix("")
            segments_layers_dir = segments_name / "layers"
            segments_layers_dir.mkdir(parents=True, exist_ok=True)

            prev = 0
            for layer_change_index, current in tqdm(
                enumerate(self.segments_layer_change_indexes),
                desc="Writing segments",
                disable=not verbose,
                total=layer_changes,
            ):
                z_fill = len(f"{layer_changes}")
                layer_number_string = f"{layer_change_index + 1}".zfill(z_fill)
                layer_path = segments_layers_dir / f"{layer_number_string}.json"
                layer_segments = segments_data[prev:current]
                with layer_path.open("w") as f:
                    json.dump(layer_segments, f, indent=2)
                prev = current

            last_layer_index = len(self.segments_layer_change_indexes)
            last_layer_path = segments_layers_dir / f"{last_layer_index + 1}.json"
            with last_layer_path.open("w") as f:
                json.dump(segments_data[prev::], f, indent=2)

            return segments_layers_dir
        else:
            # Saving segments as one giant file is not really practical so
            # it's not toggled off by default.
            with path.open("w") as f:
                _ = f.write("[\n")
                for i, segment_dict in enumerate(
                    tqdm(segments_data, desc="Writing segments", disable=not verbose)
                ):
                    json_str = json.dumps(segment_dict, indent=2)
                    indented_str = "  " + json_str.replace(
                        "\n", "\n "
                    )  # 2-space indent after [
                    _ = f.write(indented_str)
                    if i < len(segments_data) - 1:
                        _ = f.write(",\n")
                    else:
                        _ = f.write("\n")
                _ = f.write("]\n")

            return path
