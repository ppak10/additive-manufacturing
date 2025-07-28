import json
import matplotlib.pyplot as plt
import os
import shutil

from datetime import datetime
from importlib.resources import files
from pathlib import Path
from pint import Quantity, UnitRegistry
from PIL import Image
from rich import print as rprint
from tqdm import tqdm
from typing import cast, Literal

from am import data
from .config import SegmenterConfig
from .types import Command, Segment, SegmentDict


class Segmenter:
    """
    Base segmenter methods.
    """

    def __init__(
            self,
            ureg_default_system: Literal['cgs', 'mks'] = "cgs",
            ureg: UnitRegistry | None = None,
            segmenter_path: Path | None = None,
            verbose: bool | None = False,
        ):
        self.config: SegmenterConfig = SegmenterConfig(
            ureg_default_system=ureg_default_system,
            segmenter_path=segmenter_path,
            verbose=verbose
        )

        self.segments: list[Segment] = []

        self.x_min: Quantity | None = None
        self.x_max: Quantity | None = None
        self.y_min: Quantity | None = None
        self.y_max: Quantity | None = None

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
        ):
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

    def visualize(
            self,
            visualize_name: str | None = None,
            units: str = "mm"
        ) -> Path:
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

        images: list[Image.ImageFile.ImageFile] = []
        for segment_index, segment in tqdm(enumerate(self.segments), desc="Generating plots"):
            segment_index_string = f"{segment_index}".zfill(zfill)

            # Display on non-travel segments
            # TODO: Add argument to also show travel segments.
            if not segment.travel:
                ax.plot(
                    (segment.x.to(units), segment.x_next.to(units)),
                    (segment.y.to(units), segment.y_next.to(units)),
                    color="black"
                )

            frame_path = frames_out_path / f"{segment_index_string}.png"
            fig.savefig(frame_path)
            images.append(Image.open(frame_path))

        # gif_path = os.path.join("segmenters", self.filename, "layers", f"{layer_string}.gif")
        # images[0].save(gif_path, save_all=True, append_images=images[1:], duration=50, loop=0)

        # Optional: Clean up frame images
        # import shutil; shutil.rmtree(output_dir) 


    def load_segments(self, path: Path | str) -> list[Segment]:
        self.segments: list[Segment] = []

        self.x_min: Quantity | None = None
        self.x_max: Quantity | None = None
        self.y_min: Quantity | None = None
        self.y_max: Quantity | None = None

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
