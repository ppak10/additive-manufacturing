import numpy as np
import trimesh
import warnings

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from enum import Enum
from pathlib import Path
from PIL import Image
from pint import Quantity
from rich.console import Console
from shapely.geometry import LineString
from tqdm.rich import tqdm
from typing import cast, Callable, Awaitable

from am.config import BuildParameters

from .utils.infill import infill_generate, infill_visualization

# Suppress tqdm experimental warning for rich integration
warnings.filterwarnings("ignore", message=".*rich is experimental.*")


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

        self.sections = self.mesh.section_multiplane(
            plane_origin=self.mesh.bounds[0], plane_normal=[0, 0, 1], heights=z_levels
        )
        self.zfill = len(f"{len(self.sections)}")

        # sections = cast(ArrayLike, sections)

        # contour_out_path = toolpaths_out_path / "contour"
        # contour_out_path.mkdir(exist_ok=True, parents=True)
        #
        # contour_images_out_path = toolpaths_out_path / "contour" / "images"
        # contour_images_out_path.mkdir(exist_ok=True, parents=True)

        # contour_exterior_coords_out_path = toolpaths_out_path / "contour" / "exterior_coords"
        # contour_exterior_coords_out_path.mkdir(exist_ok=True, parents=True)

        # zfill = len(f"{len(sections)}")

    async def generate_infill(self, hatch_spacing=None, binary=True, num_proc=1):
        """
        Generates infill pattern for section.

        Args:
            hatch_spacing: spacing between infill rasters, millimeter units.
            binary: If True, saves as WKB format, otherwise WKT format.
            num_proc: Number of processes to use. If 1, no multiprocessing is used.
        """

        infill_data_out_path = self.toolpaths_out_path / "infill" / "data"
        infill_data_out_path.mkdir(exist_ok=True, parents=True)

        if self.sections is None:
            raise Exception("Generate sections from mesh")

        if hatch_spacing is None:
            # Defaults to loaded build parameters config.
            step = cast(Quantity, self.build_parameters.hatch_spacing).to("mm")
            hatch_spacing = step.magnitude

        total_sections = len(self.sections)

        if num_proc <= 1:
            # Single-threaded execution (original behavior)
            for section_index, section in tqdm(
                enumerate(self.sections), total=total_sections, desc="Generating infill"
            ):
                infill_index_string = f"{section_index}".zfill(self.zfill)
                infill_generate(
                    section,
                    section_index,
                    hatch_spacing,
                    infill_data_out_path,
                    infill_index_string,
                    binary,
                )
                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(section_index + 1, total_sections)
        else:
            # Multi-process execution
            args_list = []

            for section_index, section in enumerate(self.sections):
                infill_index_string = f"{section_index}".zfill(self.zfill)
                args = (
                    section,
                    section_index,
                    hatch_spacing,
                    infill_data_out_path,
                    infill_index_string,
                    binary,
                )
                args_list.append(args)

            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []
                for args in args_list:
                    future = executor.submit(infill_generate, *args)
                    futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures), total=len(futures), desc="Generating infill"
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1
                    # Report progress if callback is provided
                    if self.progress_callback:
                        await self.progress_callback(completed_count, total_sections)

        return infill_data_out_path

    async def visualize_infill(self, binary=True, num_proc=1):
        """
        Visualizes infill patterns from generated data files.

        Args:
            binary: If True, reads .wkb binary files, otherwise reads .txt WKT files
            num_proc: Number of processes to use. If 1, no multiprocessing is used.
        """
        infill_data_out_path = self.toolpaths_out_path / "infill" / "data"
        infill_images_out_path = self.toolpaths_out_path / "infill" / "images"
        infill_images_out_path.mkdir(exist_ok=True, parents=True)

        if not infill_data_out_path.exists():
            raise Exception("No infill data found. Run generate_infill() first.")

        if self.mesh is None:
            raise Exception(
                "No mesh loaded. Cannot determine bounds for consistent plotting."
            )

        # Get all infill data files
        if binary:
            infill_files = sorted(infill_data_out_path.glob("*.wkb"))
        else:
            infill_files = sorted(infill_data_out_path.glob("*.txt"))

        total_files = len(infill_files)

        if num_proc <= 1:
            # Single-threaded execution (original behavior)
            for file_index, infill_file in tqdm(
                enumerate(infill_files), total=total_files, desc="Visualizing infill"
            ):
                infill_visualization(
                    infill_file, binary, self.mesh.bounds, infill_images_out_path
                )
                # Report progress if callback is provided
                if self.progress_callback:
                    await self.progress_callback(file_index + 1, total_files)
        else:
            # Multi-process execution
            args_list = []
            for infill_file in infill_files:
                args = (infill_file, binary, self.mesh.bounds, infill_images_out_path)
                args_list.append(args)

            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []
                for args in args_list:
                    future = executor.submit(infill_visualization, *args)
                    futures.append(future)

                # Use tqdm to track progress
                completed_count = 0
                for future in tqdm(
                    as_completed(futures), total=len(futures), desc="Visualizing infill"
                ):
                    future.result()  # This will raise any exceptions that occurred
                    completed_count += 1
                    # Report progress if callback is provided
                    if self.progress_callback:
                        await self.progress_callback(completed_count, total_files)

        # Compile images into GIF
        image_files = sorted(infill_images_out_path.glob("*.png"))
        if image_files:
            # Load images into memory and close file handles
            images = []
            for img_file in tqdm(image_files, desc="Creating GIF"):
                with Image.open(img_file) as img:
                    images.append(img.copy())
            gif_path = self.toolpaths_out_path / "infill" / "infill_animation.gif"
            console = Console()
            with console.status("[bold green]Writing .gif...", spinner="dots"):
                images[0].save(
                    gif_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=200,
                    loop=0,
                )
            console.print(
                f"[bold green]✓[/bold green] GIF created: {gif_path} ({len(images)} frames)"
            )

            return gif_path

        return infill_images_out_path

    def generate_solver_segments(self):
        """
        Generates infill and contour slices for solver segment output.
        """

        # Infill

    def old(self):
        # Contour Plot
        # axis = section.plot_discrete()
        # axis = cast(Axes, axis)
        # segment_index_string = f"{section_index}".zfill(zfill)
        # contour_file = f"{segment_index_string}.png"
        # plt.savefig(contour_out_path / "images" / contour_file)
        # plt.close()

        # Infill Plot
        # fig, ax = plt.subplots(figsize=(10, 10))

        # Draw perimeter and generate infill for each polygon
        for polygon in section.polygons_full:
            # Draw perimeter
            exterior_coords = np.array(polygon.exterior.coords)

            # print(f"{section_index}, {exterior_coords}")
            # ax.add_patch(
            #     Polygon(exterior_coords, fill=False, edgecolor="green", linewidth=2)
            # )

            for interior in polygon.interiors:
                interior_coords = np.array(interior.coords)
                # ax.add_patch(
                #     Polygon(
                #         interior_coords, fill=False, edgecolor="red", linewidth=2
                #     )
                # )

            # Generate rectilinear infill (alternating 0°/90°)
            bounds = polygon.bounds
            is_horizontal = section_index % 2 == 0

            if is_horizontal:
                # Horizontal lines
                for y in np.arange(bounds[1], bounds[3], hatch_spacing.magnitude):
                    line = LineString([(bounds[0] - 1, y), (bounds[2] + 1, y)])
                    intersection = polygon.intersection(line)
                    # self._plot_infill_line(ax, intersection)
            else:
                # Vertical lines
                for x in np.arange(bounds[0], bounds[2], hatch_spacing.magnitude):
                    line = LineString([(x, bounds[1] - 1), (x, bounds[3] + 1)])
                    intersection = polygon.intersection(line)
                    # self._plot_infill_line(ax, intersection)

        # ax.set_aspect("equal")
        # ax.autoscale()
        #
        # infill_file = f"{segment_index_string}.png"
        # plt.savefig(infill_out_path / infill_file, dpi=150)
        # plt.close()

    def _plot_infill_line(self, ax, intersection):
        """Helper to plot infill line intersections."""
        if intersection.is_empty:
            return
        if intersection.geom_type == "LineString":
            x, y = intersection.xy
            ax.plot(x, y, "b-", linewidth=0.5, alpha=0.6)
        elif intersection.geom_type == "MultiLineString":
            for geom in intersection.geoms:
                x, y = geom.xy
                ax.plot(x, y, "b-", linewidth=0.5, alpha=0.6)

    def load_mesh(self, file_obj: Path, file_type: str | None = None, **kwargs):
        self.mesh = trimesh.load_mesh(file_obj, file_type, kwargs)
