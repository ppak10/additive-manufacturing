import json
import imageio.v2 as imageio
import matplotlib.pyplot as plt

from datetime import datetime
from io import BytesIO
from pathlib import Path
from pint import Quantity
from tqdm import tqdm
from typing import cast

from am.solver.segment import SolverSegment, SolverSegmentDict


class SegmenterVisualize:
    """
    Base segmenter methods.
    """

    def __init__(self):
        self.segments: list[SolverSegment] = []

        self.x_min: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.x_max: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.y_min: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.y_max: Quantity = cast(Quantity, Quantity(0.0, "m"))

    def visualize(
        self,
        segments_path: Path,
        visualization_name: str | None = None,
        color: str = "black",
        frame_format: str = "png",
        include_axis: bool = True,
        linewidth: float = 2.0,
        transparent: bool = False,
        units: str = "mm",
        verbose: bool = False,
    ) -> Path:
        """
        Provides visualization for loaded segments.
        """

        if visualization_name is None:
            visualization_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")

        visualization_path = segments_path / "visualizations" / visualization_name
        visualization_path.mkdir(exist_ok=True, parents=True)

        if len(self.segments) < 1:
            raise Exception(f"layer_index: {0} has no gcode_segments.")

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        ax.set_xlim(self.x_min.to(units).magnitude, self.x_max.to(units).magnitude)
        ax.set_ylim(self.y_min.to(units).magnitude, self.y_max.to(units).magnitude)

        ax.set_xlabel(units)
        ax.set_ylabel(units)

        zfill = len(f"{len(self.segments)}")

        # Save current frame
        frames_out_path = visualization_path / "frames"
        frames_out_path.mkdir(exist_ok=True, parents=True)

        animation_out_path = visualization_path / "frames.gif"
        writer = imageio.get_writer(animation_out_path, mode="I", duration=0.1)

        if not include_axis:
            _ = ax.axis("off")

        for segment_index, segment in tqdm(
            enumerate(self.segments),
            desc="Generating plots",
            disable=not verbose,
            total=len(self.segments),
        ):
            segment_number_string = f"{segment_index + 1}".zfill(zfill)

            # Display on non-travel segments
            # TODO: Add argument to also show travel segments.
            if not segment.travel:
                ax.plot(
                    (segment.x.to(units).magnitude, segment.x_next.to(units).magnitude),
                    (segment.y.to(units).magnitude, segment.y_next.to(units).magnitude),
                    color=color,
                    linewidth=linewidth,
                )

            frame_path = frames_out_path / f"{segment_number_string}.{frame_format}"
            fig.savefig(frame_path, transparent=transparent)

            # Copy image to memory for later
            buffer = BytesIO()
            fig.savefig(buffer, format="png", transparent=transparent)
            buffer.seek(0)
            writer.append_data(imageio.imread(buffer))

        if verbose:
            print("Writing frames to `.gif`")
        writer.close()
        return animation_out_path

    def load_segments(self, path: Path | str) -> list[SolverSegment]:
        self.segments = []

        self.x_min = cast(Quantity, Quantity(0.0, "m"))
        self.x_max = cast(Quantity, Quantity(0.0, "m"))
        self.y_min = cast(Quantity, Quantity(0.0, "m"))
        self.y_max = cast(Quantity, Quantity(0.0, "m"))

        path = Path(path)
        with path.open("r") as f:
            segments_data = cast(list[SolverSegmentDict], json.load(f))

        for seg_dict in tqdm(segments_data, desc="Loading segments"):
            segment = SolverSegment.from_dict(seg_dict)
            self.segments.append(segment)

            # Determine x_min, x_max, y_min, y_max
            if not segment.travel:
                if self.x_min is None or segment.x <= self.x_min:
                    self.x_min = segment.x
                if self.y_min is None or segment.y <= self.y_min:
                    self.y_min = segment.y
                if self.x_max is None or segment.x > self.x_max:
                    self.x_max = segment.x
                if self.y_max is None or segment.y > self.y_max:
                    self.y_max = segment.y

        return self.segments
