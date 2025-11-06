import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from pathlib import Path
from typing import Optional, Tuple, List, Union


def create_lack_of_fusion_plot(
    data_2ds: list[tuple[int, list[list[bool]]]],
    x_values: np.ndarray,
    y_values: np.ndarray,
    save_path: Union[str, Path],
    title: str = "Process Map",
    xlabel: str = "X Parameter",
    ylabel: str = "Y Parameter",
    colorbar_label: str = "Value",
    figsize: Tuple[float, float] = (4, 3),
    dpi: int = 150,
    save_dpi: int = 300,
    colormap: Optional[str] = None,
    custom_colors: Optional[List[str]] = None,
    style: str = "seaborn-v0_8-whitegrid",
    interpolation: str = "bilinear",
    show_grid: bool = True,
    transparent_bg: bool = False,
    is_boolean: bool = False,
    legend_labels: Optional[List[str]] = None,
) -> None:
    """
    Create an enhanced matplotlib process map with professional styling.
    Supports both continuous and boolean (categorical) maps.

    Parameters
    ----------
    is_boolean : bool, optional
        If True, treats data as 0/1 categorical and uses a discrete colormap.
    legend_labels : List[str], optional
        Labels for the boolean categories (only used if is_boolean=True).
        Example: ["No Lack of Fusion", "Lack of Fusion"]
    """

    # Apply style
    try:
        plt.style.use(style)
    except OSError:
        plt.style.use("default")

    plt.rcParams.update({"font.family": "Lato"})  # or any installed font
    plt.rcParams["text.color"] = "#71717A"
    plt.rcParams["axes.labelcolor"] = "#71717A"  # Axis labels (xlabel, ylabel)
    plt.rcParams["xtick.color"] = "#71717A"  # X-axis tick labels
    plt.rcParams["ytick.color"] = "#71717A"  # Y-axis tick labels
    plt.rcParams["axes.edgecolor"] = "#71717A"  # Axis lines/spines

    # plt.rcParams['legend.facecolor'] = '#047857'  # or any color
    plt.rcParams["legend.edgecolor"] = "#71717A"  # border color

    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)

    layer_heights = []
    colors = [
        "#EAB308",  # Yellow 500
        "#F97316",  # Orange 500
        "#EF4444",  # Red 500
    ]
    data_2ds.reverse()
    for layer_height, _ in data_2ds:
        layer_heights.append(layer_height)
        # color = (layer_height / 150, 0.14, 0.15, 0.5)
        # colors.append(color)
    cmap = ListedColormap(colors)

    print(data_2ds)
    for index, (layer_height, data_2d) in enumerate(data_2ds):
        # Mask all the False values so only True (1) areas are drawn
        masked_data = np.ma.masked_where(~np.array(data_2d, dtype=bool), data_2d)

        ax.imshow(
            masked_data,
            cmap=ListedColormap(colors[index]),
            origin="lower",
            extent=[x_values[0], x_values[-1], y_values[0], y_values[-1]],
            aspect="auto",
            interpolation="nearest",
        )

    # Title & labels
    if title is not None:
        ax.set_title(title, fontsize=16, fontweight="bold", pad=16)
    ax.set_xlabel(xlabel, fontsize=12, fontweight="medium", labelpad=8)
    ax.set_ylabel(ylabel, fontsize=12, fontweight="medium", labelpad=8)

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

    # Colorbar or Legend
    if is_boolean and layer_heights is not None:
        from matplotlib.patches import Patch

        handles = [
            Patch(
                facecolor=cmap.colors[i], edgecolor="k", label=f"{layer_heights[i]} µm"
            )
            for i in range(len(layer_heights))
        ]
        ax.legend(
            handles=handles,
            loc="upper right",
            frameon=True,
            fontsize=9,
            title=colorbar_label,
            title_fontsize=10,
        )
    else:
        cbar = plt.colorbar(im, ax=ax, shrink=0.85, aspect=25, pad=0.02)
        cbar.set_label(
            colorbar_label,
            rotation=270,
            labelpad=20,
            fontsize=11,
            fontweight="medium",
        )
        cbar.ax.tick_params(labelsize=9)

    # Grid & spines
    if show_grid:
        ax.grid(True, which="major", color="gray", alpha=0.3, linewidth=0.6)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_linewidth(1.2)

    plt.tight_layout()

    # Save
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(
        save_path,
        dpi=save_dpi,
        bbox_inches="tight",
        facecolor="white" if not transparent_bg else "none",
        transparent=transparent_bg,
    )
    plt.close(fig)
