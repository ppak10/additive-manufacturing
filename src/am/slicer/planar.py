import numpy as np
import trimesh

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from pathlib import Path
from pint import Quantity
from tqdm.rich import tqdm
from typing import cast, Callable, Awaitable

from am.config import BuildParameters

from .format.solver_segment import export_solver_layer
from .utils.geometry import load_geometries
from .utils.infill import infill_rectilinear
from .utils.contour import contour_generate
from .utils.visualize_2d import (
    compile_gif,
    composite_visualization,
    toolpath_visualization,
    ALPHA,
)


class SlicerOutputFolder(str, Enum):
    toolpaths = "toolpaths"


class SlicerPlanar:
    """
    Slicer for generating planar GCode from mesh input.
    """

    def __init__(
        self,
        build_parameters: BuildParameters,
        workspace_path: Path,
        run_name: str | None = None,
        progress_callback: Callable[[int, int], Awaitable[None]] | None = None,
    ):
        """
        Contains commonly reused variables for slicing.
        More state dependent to allow reslicing with different parameters.

        Args:
            build_parameters: Build parameters configuration
            workspace_path: Path to workspace directory
            run_name: Optional name for this run
            progress_callback: Optional async callback for progress reporting (current, total)
        """
        self.build_parameters = build_parameters
        self.progress_callback = progress_callback

        # Loaded in / Generated
        self.mesh: trimesh.Trimesh | None = None
        self.sections = []
        self.zfill = 0

        # Creates run folder inside workspace for slicer runs.
        if run_name is None:
            run_name = datetime.now().strftime("slicer_planar_%Y%m%d_%H%M%S")

        self.toolpaths_out_path = workspace_path / "toolpaths" / run_name
        self.toolpaths_out_path.mkdir(exist_ok=True, parents=True)

        # Save solver configs
        self.build_parameters.save(
            self.toolpaths_out_path / "configs" / "build_parameters.json"
        )

    def section_mesh(self, layer_height=None):
        """
        Sections loaded mesh using trimesh.

        Args:
            layer_height: step size for slicing, expects millimeter units.
        """

        if self.mesh is None:
            raise Exception("No mesh loaded")

        if layer_height is None:
            # Defaults to loaded build parameters config if None.
            step = cast(Quantity, self.build_parameters.layer_height).to("mm")
            layer_height = step.magnitude

        z_extents = self.mesh.bounds[:, 2]
        z_levels = np.arange(*z_extents, step=layer_height)

        # section_multiplane expects heights relative to plane_origin, not absolute z values
        plane_origin = self.mesh.bounds[0]
        heights_relative = z_levels - plane_origin[2]

        self.sections = self.mesh.section_multiplane(
            plane_origin=plane_origin, plane_normal=[0, 0, 1], heights=heights_relative
        )
        self.zfill = len(f"{len(self.sections)}")

    async def slice_sections(self, hatch_spacing=None, binary=True, num_proc=1):
        """
        Generates infill and contour patterns for section.

        Args:
            hatch_spacing: spacing between infill rasters, millimeter units.
            binary: If True, saves as WKB format, otherwise WKT format.
            num_proc: Number of processes to use. If 1, no multiprocessing is used.
        """

        infill_data_out_path = self.toolpaths_out_path / "infill" / "data"
        infill_data_out_path.mkdir(exist_ok=True, parents=True)

        contour_data_out_path = self.toolpaths_out_path / "contour" / "data"
        contour_data_out_path.mkdir(exist_ok=True, parents=True)

        if self.sections is None:
            raise Exception("Generate sections from mesh first")

        if hatch_spacing is None:
            # Defaults to loaded build parameters config.
            step = cast(Quantity, self.build_parameters.hatch_spacing).to("mm")
            hatch_spacing = step.magnitude

        total_sections = len(self.sections)

        if num_proc <= 1:
            # Single-threaded execution (original behavior)
            for section_index, section in tqdm(
                enumerate(self.sections), total=total_sections, desc="Generating slices"
            ):
                section_index_string = f"{section_index}".zfill(self.zfill)
                horizontal = section_index % 2 == 0
                infill_rectilinear(
                    section,
                    horizontal,
                    hatch_spacing,
                    infill_data_out_path,
                    section_index_string,
                    binary,
                )

                contour_generate(
                    section,
                    hatch_spacing,
                    contour_data_out_path,
                    section_index_string,
                    binary,
                )

                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(section_index + 1, total_sections)
        else:
            # Multi-process execution
            infill_args_list = []
            contour_args_list = []

            for section_index, section in enumerate(self.sections):
                section_index_string = f"{section_index}".zfill(self.zfill)
                horizontal = section_index % 2 == 0
                infill_args = (
                    section,
                    horizontal,
                    hatch_spacing,
                    infill_data_out_path,
                    section_index_string,
                    binary,
                )
                contour_args = (
                    section,
                    hatch_spacing,
                    contour_data_out_path,
                    section_index_string,
                    binary,
                )
                infill_args_list.append(infill_args)
                contour_args_list.append(contour_args)

            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []

                for args in infill_args_list:
                    future = executor.submit(infill_rectilinear, *args)
                    futures.append(future)

                for args in contour_args_list:
                    future = executor.submit(contour_generate, *args)
                    futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures), total=len(futures), desc="Generating slices"
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1
                    # Report progress if callback is provided
                    if self.progress_callback:
                        await self.progress_callback(completed_count, total_sections)

        return infill_data_out_path

    async def visualize_slices(self, binary=True, num_proc=1):
        """
        Visualizes infill patterns from generated data files.

        Args:
            binary: If True, reads .wkb binary files, otherwise reads .txt WKT files
            num_proc: Number of processes to use. If 1, no multiprocessing is used.
        """
        infill_data_out_path = self.toolpaths_out_path / "infill" / "data"
        infill_images_out_path = self.toolpaths_out_path / "infill" / "images"
        infill_images_out_path.mkdir(exist_ok=True, parents=True)

        contour_data_out_path = self.toolpaths_out_path / "contour" / "data"
        contour_images_out_path = self.toolpaths_out_path / "contour" / "images"
        contour_images_out_path.mkdir(exist_ok=True, parents=True)

        composite_images_out_path = self.toolpaths_out_path / "composite" / "images"
        composite_images_out_path.mkdir(exist_ok=True, parents=True)

        if not infill_data_out_path.exists() or not contour_data_out_path.exists():
            raise Exception("Slice data not found. Run slice_sections() first.")

        if self.mesh is None:
            raise Exception(
                "No mesh loaded. Cannot determine bounds for consistent plotting."
            )

        # Get all infill data files
        if binary:
            infill_files = sorted(infill_data_out_path.glob("*.wkb"))
            contour_files = sorted(contour_data_out_path.glob("*.wkb"))
        else:
            infill_files = sorted(infill_data_out_path.glob("*.txt"))
            contour_files = sorted(contour_data_out_path.glob("*.txt"))

        total_files = len(infill_files)

        if num_proc <= 1:
            # Single-threaded execution (original behavior)
            for file_index, infill_file in tqdm(
                enumerate(infill_files), total=total_files, desc="Visualizing infill"
            ):
                toolpath_visualization(
                    infill_file,
                    binary,
                    self.mesh.bounds,
                    infill_images_out_path,
                    ALPHA,
                    "orange",
                )
                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(file_index + 1, total_files)
            for file_index, contour_file in tqdm(
                enumerate(contour_files), total=total_files, desc="Visualizing contour"
            ):
                toolpath_visualization(
                    contour_file, binary, self.mesh.bounds, contour_images_out_path
                )
                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(file_index + 1, total_files)
            for file_index, (infill_file, contour_file) in tqdm(
                enumerate(zip(infill_files, contour_files)),
                total=total_files,
                desc="Visualizing composite",
            ):
                composite_visualization(
                    infill_file,
                    contour_file,
                    binary,
                    self.mesh.bounds,
                    composite_images_out_path,
                )
                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(file_index + 1, total_files)
            # Compile images into GIF
            infill_gif_path = self.toolpaths_out_path / "infill" / "animation.gif"
            compile_gif(infill_images_out_path, infill_gif_path)

            contour_gif_path = self.toolpaths_out_path / "contour" / "animation.gif"
            compile_gif(contour_images_out_path, contour_gif_path)

            composite_gif_path = self.toolpaths_out_path / "composite" / "animation.gif"
            compile_gif(composite_images_out_path, composite_gif_path)

        else:
            # Multi-process execution
            infill_args_list = []
            contour_args_list = []
            composite_args_list = []

            for infill_file in infill_files:
                infill_args = (
                    infill_file,
                    binary,
                    self.mesh.bounds,
                    infill_images_out_path,
                    ALPHA,
                    "orange",
                )
                infill_args_list.append(infill_args)

            for contour_file in contour_files:
                contour_args = (
                    contour_file,
                    binary,
                    self.mesh.bounds,
                    contour_images_out_path,
                )
                contour_args_list.append(contour_args)

            for infill_file, contour_file in zip(infill_files, contour_files):
                composite_args = (
                    infill_file,
                    contour_file,
                    binary,
                    self.mesh.bounds,
                    composite_images_out_path,
                )
                composite_args_list.append(composite_args)

            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []

                for args in infill_args_list:
                    future = executor.submit(toolpath_visualization, *args)
                    futures.append(future)

                for args in contour_args_list:
                    future = executor.submit(toolpath_visualization, *args)
                    futures.append(future)

                for args in composite_args_list:
                    future = executor.submit(composite_visualization, *args)
                    futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures), total=len(futures), desc="Visualizing slices"
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1
                    # Report progress if callback is provided
                    if self.progress_callback:
                        await self.progress_callback(completed_count, total_files)

                # Compile images into GIF
                futures = []
                infill_gif_path = self.toolpaths_out_path / "infill" / "animation.gif"
                future = executor.submit(
                    compile_gif, infill_images_out_path, infill_gif_path
                )
                futures.append(future)

                contour_gif_path = self.toolpaths_out_path / "contour" / "animation.gif"
                future = executor.submit(
                    compile_gif, contour_images_out_path, contour_gif_path
                )
                futures.append(future)

                composite_gif_path = (
                    self.toolpaths_out_path / "composite" / "animation.gif"
                )
                future = executor.submit(
                    compile_gif, composite_images_out_path, composite_gif_path
                )
                futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Compiling .gif files",
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1

        return composite_gif_path

    async def export_solver_segments(self, binary=True, num_proc=1):
        """
        Exports sliced geometries to solver segment.
        """
        infill_data_out_path = self.toolpaths_out_path / "infill" / "data"
        contour_data_out_path = self.toolpaths_out_path / "contour" / "data"

        solver_data_out_path = self.toolpaths_out_path / "solver" / "data"
        solver_data_out_path.mkdir(exist_ok=True, parents=True)

        if not infill_data_out_path.exists() or not contour_data_out_path.exists():
            raise Exception("Slice data not found. Run slice_sections() first.")

        if self.mesh is None:
            raise Exception(
                "No mesh loaded. Cannot determine bounds for consistent plotting."
            )

        # Get all infill data files
        if binary:
            infill_files = sorted(infill_data_out_path.glob("*.wkb"))
            contour_files = sorted(contour_data_out_path.glob("*.wkb"))
        else:
            infill_files = sorted(infill_data_out_path.glob("*.txt"))
            contour_files = sorted(contour_data_out_path.glob("*.txt"))

        layer_count = min(len(infill_files), len(contour_files))

        if num_proc <= 1:
            # Single-threaded execution (original behavior)
            for layer_index in tqdm(range(layer_count), desc="Exporting solver layers"):
                contour_file = contour_files[layer_index]
                infill_file = infill_files[layer_index]
                contour_geometries = load_geometries(
                    file_path=contour_file, binary=binary
                )
                infill_geometries = load_geometries(
                    file_path=infill_file, binary=binary
                )
                geometries = [*contour_geometries, *infill_geometries]
                export_solver_layer(
                    solver_data_out_path, geometries, layer_index, layer_count
                )
        else:
            # Multi-process execution
            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []

                for layer_index in range(layer_count):
                    contour_file = contour_files[layer_index]
                    infill_file = infill_files[layer_index]
                    contour_geometries = load_geometries(
                        file_path=contour_file, binary=binary
                    )
                    infill_geometries = load_geometries(
                        file_path=infill_file, binary=binary
                    )
                    geometries = [*contour_geometries, *infill_geometries]
                    future = executor.submit(
                        export_solver_layer,
                        solver_data_out_path,
                        geometries,
                        layer_index,
                        layer_count,
                    )
                    futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Exporting solver layers",
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1
                    # Report progress if callback is provided
                    if self.progress_callback:
                        await self.progress_callback(completed_count, layer_count)

        return solver_data_out_path

    def load_mesh(
        self, file_obj: Path, file_type: str | None = None, units: str = "mm", **kwargs
    ):
        """
        Load a mesh from file with optional unit conversion.

        Args:
            file_obj: Path to mesh file
            file_type: Optional file type specification
            units: Units of the input file ('mm' or 'inch'). Default is 'mm'.
                   If 'inch', mesh will be scaled to mm internally.
            **kwargs: Additional arguments passed to trimesh.load_mesh
        """
        self.mesh = trimesh.load_mesh(file_obj, file_type, kwargs)

        # Convert from inches to mm if needed
        if units.lower() in ["inch", "inches", "in"]:
            self.mesh.apply_scale(25.4)
