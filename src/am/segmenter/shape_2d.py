import json

from enum import Enum
from pathlib import Path
from pint import Quantity
from typing import cast
from tqdm import tqdm

from am.solver.segment import SolverSegment


class Shape(str, Enum):
    line = "line"
    square = "square"
    circle = "circle"


class SegmenterShape2D:
    """
    Generates a simple tool path given a simple shape argument.
    """

    def __init__(self):
        self.segments: list[SolverSegment] = []

    def generate(
        self,
        shape: Shape = Shape.line,
        size: float = 10.0,
        distance_xy_max: float = 1.0,
        units: str = "mm",
    ):
        """
        Generates shape with a given size
        """

        max_segment_length = Quantity(distance_xy_max, units)

        match shape:
            case Shape.line:
                distance_xy = Quantity(size, units)

                # Divides `distance_xy` into segments split by `max_segment_length`
                quotient, remainder = divmod(distance_xy, max_segment_length)
                num_segments = int(quotient)
                segment_distances = [max_segment_length] * num_segments

                # Adds one more segment to account for remainder.
                if remainder > 0:
                    num_segments += 1
                    segment_distances.append(remainder)

                y = cast(Quantity, Quantity(5.0, units))
                prev_x = cast(Quantity, Quantity(0.0, units))
                for segment_index, segment_distance in enumerate(segment_distances):
                    next_x = cast(Quantity, prev_x + segment_distance)

                    segment = SolverSegment(
                        x=prev_x,
                        y=y,
                        z=cast(Quantity, Quantity(0.0, units)),
                        e=cast(Quantity, Quantity(1.0, units)),
                        x_next=next_x,
                        y_next=y,
                        z_next=cast(Quantity, Quantity(0.0, units)),
                        e_next=cast(Quantity, Quantity(1.0, units)),
                        angle_xy=cast(Quantity, Quantity(0.0, "radians")),
                        distance_xy=cast(Quantity, segment_distance),
                        travel=False,
                    )

                    self.segments.append(segment)
                    prev_x = next_x

                return self.segments

            case _:
                print("not implemented yet")

    def save_segments(
        self,
        segments_path: Path,
        segments: list[SolverSegment] | None = None,
        verbose: bool | None = False,
    ) -> Path:

        if segments is None:
            segments = self.segments

        segments_data = [
            segment.to_dict()
            for segment in tqdm(
                segments, desc="Serializing segments", disable=not verbose
            )
        ]

        layer_path = segments_path / "layers" / "1.json"
        layer_path.parent.mkdir(parents=True, exist_ok=True)

        with layer_path.open("w") as f:
            json.dump(segments_data, f, indent=2)

        return layer_path
