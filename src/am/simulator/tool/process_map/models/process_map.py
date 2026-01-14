import matplotlib.pyplot as plt
import numpy as np

from concurrent.futures import ProcessPoolExecutor, as_completed
from copy import deepcopy
from itertools import product
from matplotlib.patches import Patch
from msgpack import packb, unpackb
from pathlib import Path
from pint import Quantity
from pydantic import BaseModel, PrivateAttr
from typing_extensions import cast, TypedDict
from tqdm.rich import tqdm

from am.config import BuildParameters, BuildParametersDict, Material, MaterialDict

from .process_map_parameter_range import (
    ProcessMapParameterRange,
    ProcessMapParameterRangeDict,
)
from .process_map_data_point import ProcessMapDataPoint
from .process_map_parameter import ProcessMapParameter
from .process_map_plot_data import ProcessMapPlotData


class ProcessMapDict(TypedDict):
    build_parameters: BuildParametersDict
    material: MaterialDict

    parameter_ranges: list[ProcessMapParameterRangeDict]
    out_path: Path


class ProcessMap(BaseModel):
    """
    Process Map class for generating lack of fusion predictions of material.
    """

    build_parameters: BuildParameters
    material: Material

    parameter_ranges: list[ProcessMapParameterRange]
    out_path: Path

    # Private field to cache data points
    _data_points: list[ProcessMapDataPoint] | None = PrivateAttr(default=None)
    _plot_data: ProcessMapPlotData | None = PrivateAttr(default=None)

    def run(self, num_proc: int = 1):
        # Avoids circular import
        from am.simulator.tool.process_map.utils import run_process_map_data_point

        if self._data_points is None:
            # Runs initial computation to compile list of data points for when
            # self._data_points is not initialized.
            _data_points = self.data_points
        else:
            _data_points = self._data_points

        data_points_updated = []

        if num_proc <= 1:

            # Iterates through points z (inner) -> y (middle) -> x (outer)
            for data_point in tqdm(_data_points, desc="Running Process Map"):
                # Copies build parameters to a new object to pass as overrides.
                modified_build_parameters = deepcopy(self.build_parameters)

                for parameter in data_point.parameters:
                    name = parameter.name
                    value = parameter.value
                    modified_build_parameters.__setattr__(name, value)

                data_point = run_process_map_data_point(
                    modified_build_parameters,
                    self.material,
                    data_point,
                )

                data_points_updated.append(data_point)
        else:
            # Multi-process execution
            args_list = []

            for data_point in _data_points:
                # Copies build parameters to a new object to pass as overrides.
                modified_build_parameters = deepcopy(self.build_parameters)

                for parameter in data_point.parameters:
                    name = parameter.name
                    value = parameter.value
                    modified_build_parameters.__setattr__(name, value)

                args = (modified_build_parameters, self.material, data_point)
                args_list.append(args)

            with ProcessPoolExecutor(max_workers=num_proc) as executor:
                futures = []
                for args in args_list:
                    future = executor.submit(run_process_map_data_point, *args)
                    futures.append(future)

                # Use tqdm to track progress
                for future in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Running Process Map",
                ):
                    result = (
                        future.result()
                    )  # This will raise any exceptions that occurred
                    data_points_updated.append(result)

        self._data_points = data_points_updated

        return data_points_updated

    @property
    def plot_data(self) -> ProcessMapPlotData:
        """
        Converts 1D array of data points to 2D or 3D parameters grid.
        Intended for organizing points to best plot values.
        Assumes uniform grid.
        """

        if self._plot_data is not None:
            return self._plot_data

        if self._data_points is None:
            raise Exception(
                "Process map needs to be run before plot data can be generated."
            )

        _data_points = self._data_points

        # Assumes parameters are listed as [x, y, z]
        parameter_names = [p.name for p in self.parameter_ranges]

        # Creates index dictionary for fast reference when creating grid.
        axis_dict = {}
        for parameter_name in parameter_names:
            axis_dict[parameter_name] = {}

        axis_sets = [set() for _ in self.parameter_ranges]

        # Creates axis sets of all data point values along each x, y, and z.
        for data_point in _data_points:
            for index in range(len(self.parameter_ranges)):
                value = data_point.parameters[index].value
                axis_set = axis_sets[index]

                if value not in axis_set:
                    axis_set.add(value)

        # Sorts sets into lists for plotting.
        axis_lists = []

        # Sorts axes and creates index dictionary.
        for axis_set_index, axis_set in enumerate(axis_sets):
            parameter_name = parameter_names[axis_set_index]

            axis_list = sorted(list(axis_set))
            axis_lists.append(axis_list)

            for index, axis_item in enumerate(axis_list):
                axis_magnitude = axis_item.magnitude
                axis_dict[parameter_name][axis_magnitude] = index

        # Initialize grid with shape based on axis_lists
        shape = tuple(len(axis_list) for axis_list in axis_lists)
        grid = np.full(shape, None, dtype=object)

        # Populate grid in one loop
        for data_point in _data_points:
            # Obtains a tuple of parameter values to then utilize as index.
            # i.e. (1, 2, 1) for say (100, 200, 100) as index for grid.
            indices = tuple(
                axis_dict[parameter.name][
                    int(cast(Quantity, parameter.value).magnitude)
                ]
                for parameter in data_point.parameters
            )
            # print(indices)

            grid[indices] = data_point

        plot_data = ProcessMapPlotData(
            axes=axis_lists, grid=grid, parameter_names=parameter_names
        )

        self._plot_data = plot_data

        return plot_data

    @property
    def data_points(self) -> list[ProcessMapDataPoint]:
        """
        Generate all data points from the parameter ranges using a cartesian product.
        Caches the result after first generation or loading from file.

        Returns:
            List of ProcessMapDataPoint objects with all parameter combinations.
        """

        # If we have cached data points, return those
        if self._data_points is not None:
            return self._data_points

        # Build arrays of values for each parameter range
        ranges = []
        names = []
        units = []

        for parameter_range in self.parameter_ranges:
            # Generate numpy array of values from start to stop with step
            step = cast(Quantity, parameter_range.step).magnitude
            start = cast(Quantity, parameter_range.start).magnitude

            # Add half step to include stop
            stop = cast(Quantity, parameter_range.stop).magnitude + step / 2
            values = np.arange(start, stop, step)

            ranges.append(values)
            names.append(parameter_range.name)
            units.append(parameter_range.units)

        # Generate cartesian product of all parameter values
        data_points = []
        for combination in product(*ranges):
            parameters = []

            for name, value, unit in zip(names, combination, units):
                # Create ProcessMapParameter with the value and units from the range
                param = ProcessMapParameter(
                    name=name, value=cast(Quantity, Quantity(value, unit))
                )
                parameters.append(param)

            # Create data point with these parameters
            data_point = ProcessMapDataPoint(
                parameters=parameters, melt_pool_dimensions=None, labels=None
            )
            data_points.append(data_point)

        # Cache the generated data points
        self._data_points = data_points
        return data_points

    def plot(
        self,
        file_path: Path | None = None,
        figsize: tuple[float, float] = (4, 3),
        dpi: int = 600,
        transparent_bg: bool = True,
    ):
        # Avoids circular import
        from am.simulator.tool.process_map.utils import get_colormap_segment

        if self._plot_data is None:
            # Compile plot data if not done already.
            _plot_data = self.plot_data
        else:
            _plot_data = self._plot_data

        # Colors
        # plt.rcParams.update({"font.family": "Lato"})  # or any installed font
        plt.rcParams["text.color"] = "#71717A"
        plt.rcParams["axes.labelcolor"] = "#71717A"  # Axis labels (xlabel, ylabel)
        plt.rcParams["xtick.color"] = "#71717A"  # X-axis tick labels
        plt.rcParams["ytick.color"] = "#71717A"  # Y-axis tick labels
        plt.rcParams["axes.edgecolor"] = "#71717A"  # Axis lines/spines
        plt.rcParams["legend.edgecolor"] = "#71717A"  # border color

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

        # Ticks
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=10,
            direction="in",
            length=6,
            width=1,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            labelsize=8,
            direction="in",
            length=3,
            width=0.75,
        )

        # Axis Labels

        x_units = f"{_plot_data.axes[1][0].units:~}"
        x_label = _plot_data.parameter_names[1].replace("_", " ").title()
        ax.set_xlabel(f"{x_label} ({x_units})")

        y_units = f"{_plot_data.axes[0][0].units:~}"
        y_label = _plot_data.parameter_names[0].replace("_", " ").title()
        ax.set_ylabel(f"{y_label} ({y_units})")

        # Handle 2D vs 3D grids
        extent = cast(
            tuple[float, float, float, float],
            (
                _plot_data.axes[1][0].magnitude,
                _plot_data.axes[1][-1].magnitude,
                _plot_data.axes[0][0].magnitude,
                _plot_data.axes[0][-1].magnitude,
            ),
        )

        # TODO: Support multiple types of labels
        # Extract data for plotting.
        cmap = plt.get_cmap("plasma")
        data = np.zeros(_plot_data.grid.shape)

        for index in np.ndindex(_plot_data.grid.shape):
            point = _plot_data.grid[index]

            if point is not None:
                data[index] = "lack_of_fusion" in point.labels
            else:
                data[index] = np.nan

        if len(_plot_data.grid.shape) == 2:
            # 2D grid: simple heatmap
            ax.imshow(
                data, cmap="viridis", aspect="auto", origin="lower", extent=extent
            )

        elif len(_plot_data.grid.shape) == 3:
            # 3D grid: overlay plots along z-axis
            handles = []
            max_z_value_magnitude = _plot_data.axes[2][-1].magnitude

            # z is often layer height or hatch spacing
            z_values = _plot_data.axes[2]
            z_values.reverse()

            z_units = f"{_plot_data.axes[2][0].units:~}"
            z_label = _plot_data.parameter_names[2].replace("_", " ").title()

            for z_idx, z_value in enumerate(z_values):
                # Legend
                position = z_value.magnitude / max_z_value_magnitude

                handles.append(
                    Patch(
                        facecolor=cmap(position),
                        edgecolor="k",
                        label=f"{z_value.magnitude} ({z_units})",
                    )
                )

                # Create colormap segment for this layer
                layer_cmap = get_colormap_segment(position, cmap)

                # Plotting
                data_2d = data[:, :, -z_idx]
                # Mask all the False values so only True (1) areas are drawn
                data_2d_masked = np.ma.masked_where(
                    ~np.array(data_2d, dtype=bool), data_2d
                )
                ax.imshow(
                    data_2d_masked,
                    cmap=layer_cmap,
                    aspect="auto",
                    origin="lower",
                    extent=extent,
                    interpolation="nearest",
                )

            ax.legend(
                handles=handles,
                loc="upper right",
                frameon=True,
                fontsize=9,
                title=z_label,
                title_fontsize=10,
            )

        if file_path is None:
            file_path = self.out_path / "process_map.png"

        plt.savefig(
            file_path,
            dpi=dpi,
            bbox_inches="tight",
            facecolor="white" if not transparent_bg else "none",
            transparent=transparent_bg,
        )
        plt.close(fig)

    def save(self, file_path: Path | None = None) -> Path:
        """
        Save process map configuration using messagepack, including all fields.

        Args:
            file_path: Optional path to save

        Returns:
            Path to the saved configuration file
        """

        if file_path is None:
            file_path = self.out_path / "process_map.msgpack"

        data = self.model_dump(mode="json")
        packed: bytes = cast(bytes, packb(data, use_bin_type=True))

        with open(file_path, "wb") as f:
            f.write(packed)

        return file_path

    @classmethod
    def load(cls, file_path: Path, progress_callback=None) -> "ProcessMap":
        """
        Load process map configuration using messagepack.

        Args:
            file_path: Path to the process_map.msgpack file
            progress_callback: Optional progress callback to attach

        Returns:
            Process map instance with loaded configuration
        """

        with open(file_path, "rb") as f:
            # raw=False decodes binary strings to unicode
            data = unpackb(f.read(), raw=False)

        # Convert out_path string back to Path
        if "out_path" in data and isinstance(data["out_path"], str):
            data["out_path"] = Path(data["out_path"])

        # Create the ProcessMap instance using the validated data.
        # Pydantic's model_validate will handle populating the public fields.
        # Private fields (_data_points, _plot_data) will be initialized to their defaults (None).
        process_map = cls.model_validate(data)

        return process_map
