import matplotlib.pyplot as plt
import numpy as np

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from pathlib import Path
from typing import cast, Literal

from .models import ProcessMapPlotData

PlotType = Literal["lack_of_fusion"]


def get_colormap_segment(
    position: float, base_cmap, width: float = 0.2
) -> LinearSegmentedColormap:
    """
    Create a colormap segment centered around a position in the base colormap.

    Args:
        position: Normalized position (0-1) in the base colormap
        base_cmap: Base colormap to extract segment from
        width: Width of the segment to extract (default 0.2)

    Returns:
        A new colormap with colors from the segment
    """
    n_colors = 256
    colors = [
        base_cmap(position + (i / n_colors - 0.5) * width) for i in range(n_colors)
    ]
    return LinearSegmentedColormap.from_list("custom", colors)


def plot_process_map(
    process_map_path: Path,
    plot_data: ProcessMapPlotData,
    plot_type: PlotType,
    flip_xy: bool = False,
    figsize: tuple[float, float] = (4, 3),
    dpi: int = 600,
    transparent_bg: bool = True,
):
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

    x_units = f"{plot_data.axes[1][0].units:~}"
    x_label = plot_data.parameters[1].replace("_", " ").title()
    ax.set_xlabel(f"{x_label} ({x_units})")

    y_units = f"{plot_data.axes[0][0].units:~}"
    y_label = plot_data.parameters[0].replace("_", " ").title()
    ax.set_ylabel(f"{y_label} ({y_units})")

    # Handle 2D vs 3D grids
    extent = cast(
        tuple[float, float, float, float],
        (
            plot_data.axes[1][0].magnitude,
            plot_data.axes[1][-1].magnitude,
            plot_data.axes[0][0].magnitude,
            plot_data.axes[0][-1].magnitude,
        ),
    )

    if plot_type == "lack_of_fusion":
        # Extract data for plotting.
        cmap = plt.get_cmap("plasma")
        data = np.zeros(plot_data.grid.shape)

        for index in np.ndindex(plot_data.grid.shape):
            point = plot_data.grid[index]

            if point is not None:
                data[index] = point.melt_pool_classifications.lack_of_fusion
            else:
                data[index] = np.nan

        if len(plot_data.grid.shape) == 2:
            # 2D grid: simple heatmap
            ax.imshow(
                data, cmap="viridis", aspect="auto", origin="lower", extent=extent
            )

        elif len(plot_data.grid.shape) == 3:
            # 3D grid: overlay plots along z-axis
            handles = []
            max_z_value_magnitude = plot_data.axes[2][-1].magnitude

            # z is often layer height or hatch spacing
            z_values = plot_data.axes[2]
            z_values.reverse()

            z_units = f"{plot_data.axes[2][0].units:~}"
            z_label = plot_data.parameters[2].replace("_", " ").title()

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

    save_path = process_map_path / "plots" / "lack_of_fusion.png"
    plt.savefig(
        save_path,
        dpi=dpi,
        bbox_inches="tight",
        facecolor="white" if not transparent_bg else "none",
        transparent=transparent_bg,
    )
    plt.close(fig)
