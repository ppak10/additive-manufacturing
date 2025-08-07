import json
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import os
import shutil

from datetime import datetime
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from pint import Quantity, UnitRegistry
from rich import print as rprint
from tqdm import tqdm
from typing import cast, Literal

from am import data
from am.workspace.config import WorkspaceConfig
from .config import SegmenterConfig
from .types import Segment, SegmentDict


class Segmenter:
    """
    Base segmenter methods.
    """

    def __init__(
        self,
        ureg_default_system: Literal["cgs", "mks"] = "cgs",
        ureg: UnitRegistry | None = None,
        segmenter_path: Path | None = None,
        verbose: bool | None = False,
    ):
        self.config: SegmenterConfig = SegmenterConfig(
            ureg_default_system=ureg_default_system,
            segmenter_path=segmenter_path,
            verbose=verbose,
        )

        self.segments: list[Segment] = []

        self.x_min: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.x_max: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.y_min: Quantity = cast(Quantity, Quantity(0.0, "m"))
        self.y_max: Quantity = cast(Quantity, Quantity(0.0, "m"))

    @property
    def ureg(self):
        return self.config.ureg

    @property
    def segmenter_path(self):
        return self.config.segmenter_path

    @segmenter_path.setter
    def segmenter_path(self, value: Path):
        self.config.segmenter_path = value

    @property
    def verbose(self):
        return self.config.verbose

    def copy_example_parts(self, segmenter_path: Path):
        parts_resource_dir = files(data) / "segmenter" / "parts"
        parts_dest_dir = segmenter_path / "parts"
        parts_dest_dir.mkdir(parents=True, exist_ok=True)

        for entry in parts_resource_dir.iterdir():
            if entry.is_file():
                dest_file = parts_dest_dir / entry.name
                with entry.open("rb") as src, open(dest_file, "wb") as dst:
                    shutil.copyfileobj(src, dst)

    def initialize(
        self,
        segmenter_path: Path,
        include_examples: bool | None = True,
    ) -> SegmenterConfig:
        # Create `segmenter` folder
        segmenter_path.mkdir(exist_ok=True)
        self.config.segmenter_path = segmenter_path
        segmenter_config_file = self.config.save()
        rprint(f"Segmenter config file saved at: {segmenter_config_file}")

        # Create `segmenter/parts` directory
        segmenter_parts_path = self.config.segmenter_path / "parts"
        os.makedirs(segmenter_parts_path, exist_ok=True)

        if include_examples:
            self.copy_example_parts(segmenter_path)

        return self.config 

    def visualize(
        self,
        visualize_name: str | None = None,
        color: str = "black",
        frame_format: str = "png",
        include_axis: bool = True,
        linewidth: float = 2.0,
        transparent: bool = False,
        units: str = "mm",
        verbose: bool = False,
    ):
        """
        Provides visualization for loaded segments.
        """

        if visualize_name is None:
            visualize_name = datetime.now().strftime("run_%Y%m%d_%H%M%S")

        cwd = Path.cwd()
        visualize_out_path = cwd / "segmenter" / "visualizations" / visualize_name
        visualize_out_path.mkdir(exist_ok=True, parents=True)

        if len(self.segments) < 1:
            raise Exception(f"layer_index: {0} has no gcode_segments.")

        fig, ax = plt.subplots(1, 1, figsize=(10, 5))

        ax.set_xlim(self.x_min.to(units).magnitude, self.x_max.to(units).magnitude)
        ax.set_ylim(self.y_min.to(units).magnitude, self.y_max.to(units).magnitude)

        ax.set_xlabel(units)
        ax.set_ylabel(units)

        zfill = len(f"{len(self.segments)}")

        # Save current frame
        frames_out_path = visualize_out_path / "frames"
        frames_out_path.mkdir(exist_ok=True, parents=True)

        animation_out_path = visualize_out_path / "frames.gif"
        writer = imageio.get_writer(animation_out_path, mode="I", duration=0.1)

        if not include_axis:
            _ = ax.axis("off")

        for segment_index, segment in tqdm(
            enumerate(self.segments),
            desc="Generating plots",
            disable=not verbose,
            total=len(self.segments),
        ):
            segment_index_string = f"{segment_index}".zfill(zfill)

            # Display on non-travel segments
            # TODO: Add argument to also show travel segments.
            if not segment.travel:
                ax.plot(
                    (segment.x.to(units).magnitude, segment.x_next.to(units).magnitude),
                    (segment.y.to(units).magnitude, segment.y_next.to(units).magnitude),
                    color=color,
                    linewidth=linewidth,
                )

            frame_path = frames_out_path / f"{segment_index_string}.{frame_format}"
            fig.savefig(frame_path, transparent=transparent)

            # Copy image to memory for later
            buffer = BytesIO()
            fig.savefig(buffer, format="png", transparent=transparent)
            buffer.seek(0)
            writer.append_data(imageio.imread(buffer))

        writer.close()

    @classmethod
    def list_parts(cls, workspace: str, out_path: Path | None = None) -> list[str] | None:
        """
        Lists workspace directories within out_path
        """
        if out_path is None:
            project_root = WorkspaceConfig.get_project_root_from_package()
            out_path = project_root / "out"

        if not out_path.exists() or not out_path.is_dir():
            return None

        segmenter_parts_path = out_path / workspace / "segmenter" / "parts"

        return [
            partfile.name
            for partfile in segmenter_parts_path.iterdir()
            if partfile.is_file() and partfile.suffix == ".gcode"
        ]

    def load_segments(self, path: Path | str) -> list[Segment]:
        self.segments = []

        self.x_min = cast(Quantity, Quantity(0.0, "m"))
        self.x_max = cast(Quantity, Quantity(0.0, "m"))
        self.y_min = cast(Quantity, Quantity(0.0, "m"))
        self.y_max = cast(Quantity, Quantity(0.0, "m"))

        path = Path(path)
        with path.open("r") as f:
            segments_data = cast(list[SegmentDict], json.load(f))

        for seg_dict in tqdm(segments_data, desc="Loading segments"):
            segment = Segment.from_dict(seg_dict)
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
