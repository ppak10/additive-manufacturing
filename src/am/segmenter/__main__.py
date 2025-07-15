import os
import shutil

from importlib.resources import files
from pathlib import Path
from pint import UnitRegistry
from rich import print as rprint
from typing import Literal

from am import data
from .config import SegmenterConfig


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

    def create_segmenter(
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
 
