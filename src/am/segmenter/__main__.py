import os

# import shutil

# from importlib.resources import files
from pathlib import Path
from pint import UnitRegistry
from rich import print as rprint
from typing import Literal

# from am import data
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

    def create_segmenter(self, segmenter_path: Path , force: bool | None = False):
        # Create the `out` directory if it doesn't exist.
        segmenter_path.mkdir(exist_ok=True)
        self.config.segmenter_path = segmenter_path
        segmenter_config_file = self.config.save()
        rprint(f"Segmenter config file saved at: {segmenter_config_file}")

        # Copy manage.py
        # resource_path = os.path.join("segmenter", "manage.py")
        # manage_py_resource_path = files(data).joinpath(resource_path)
        # manage_py_segmenter_path = os.path.join(self.segmenter_path, "manage.py")
        # shutil.copy(manage_py_resource_path, manage_py_segmenter_path)

        # Create parts directory
        # segmenter_parts_path = os.path.join(self.config.segmenter_path, "parts")
        # os.makedirs(segmenter_parts_path, exist_ok=True)

        # resource_path = os.path.join("segmenter", "parts", "README.md")
        # README_md_resource_path = files(data).joinpath(resource_path)
        # README_md_segmenter_path = os.path.join(self.segmenter_path, "parts", "README.md")
        # shutil.copy(README_md_resource_path, README_md_segmenter_path)

 
