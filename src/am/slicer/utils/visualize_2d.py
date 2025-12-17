import matplotlib
import matplotlib.pyplot as plt

from pathlib import Path
from PIL import Image
from rich.console import Console
from shapely import wkb, wkt
from tqdm.rich import tqdm

matplotlib.use("Agg")  # Use non-interactive backend

ALPHA = 0.8
COLOR = "red"
DPI = 600
LINESTYLE = "solid"
LINEWIDTH = 1.5
PADDING = 1.0


def load_geometries(file_path: Path, binary: bool):
    """
    Load geometries from a toolpath file.
    """

    geometries = []
    if binary:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        g_bytes = bytes.fromhex(line)
                        geometries.append(wkb.loads(g_bytes))
                    except Exception as e:
                        print(
                            f"Warning: Skipping malformed geometry in {file_path.name}: {e}"
                        )
    else:
        with open(file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    geometries.append(wkt.loads(line))
    return geometries


def plot_geometries(
    ax,
    geometries,
    color: str = COLOR,
    linewidth: float = LINEWIDTH,
    alpha: float = ALPHA,
    linestyle: str = LINESTYLE,
):
    """
    Plot geometries on the given axis.
    """
    for geometry in geometries:
        if geometry.is_empty:
            continue
        if geometry.geom_type == "LineString":
            x, y = geometry.xy
            ax.plot(
                x, y, color=color, linewidth=linewidth, alpha=alpha, linestyle=linestyle
            )
        elif geometry.geom_type == "MultiLineString":
            for geom in geometry.geoms:
                x, y = geom.xy
                ax.plot(
                    x,
                    y,
                    color=color,
                    linewidth=linewidth,
                    alpha=alpha,
                    linestyle=linestyle,
                )


def set_axis_bounds(ax, mesh_bounds, padding: float = PADDING):
    """
    Set axis bounds with optional padding and formatting.
    """

    x_max = abs(mesh_bounds[0, 0]) + abs(mesh_bounds[1, 0])
    y_max = abs(mesh_bounds[0, 1]) + abs(mesh_bounds[1, 1])

    ax.set_xlim(-padding, x_max + padding)
    ax.set_ylim(-padding, y_max + padding)
    ax.set_aspect("equal")

    # Set axis labels
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")

    # Set tick marks to point inward
    ax.tick_params(direction="in", which="both")


def composite_visualization(
    infill_file,
    contour_file,
    binary,
    mesh_bounds,
    composite_images_out_path,
    contour_alpha: float = ALPHA,
    contour_color: str = COLOR,
    contour_linestyle: str = LINESTYLE,
    contour_linewidth: float = LINEWIDTH,
    infill_alpha: float = ALPHA,
    infill_color: str = "orange",
    infill_linestyle: str = LINESTYLE,
    infill_linewidth: float = LINEWIDTH,
    dpi: int = DPI,
    padding: float = PADDING,
):
    """
    Plots the infill and contour files for composite visualization.
    """

    # Load geometries from both files
    infill_geometries = load_geometries(infill_file, binary)
    contour_geometries = load_geometries(contour_file, binary)

    # Create visualization
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot contour lines and infill lines
    plot_geometries(
        ax,
        contour_geometries,
        contour_color,
        contour_linewidth,
        contour_alpha,
        contour_linestyle,
    )

    plot_geometries(
        ax,
        infill_geometries,
        infill_color,
        infill_linewidth,
        infill_alpha,
        infill_linestyle,
    )

    # Set consistent bounds across all layers using mesh bounds with padding
    set_axis_bounds(ax, mesh_bounds, padding)

    # Set title with layer number
    layer_number = infill_file.stem
    ax.set_title(f"Composite (Layer {layer_number})")

    # Save image with same base name as data file
    image_file = infill_file.stem + ".png"
    plt.savefig(composite_images_out_path / image_file, dpi=dpi)
    plt.close()

    return infill_file.name


def toolpath_visualization(
    toolpath_file,
    binary,
    mesh_bounds,
    images_out_path,
    alpha: float = ALPHA,
    color: str = COLOR,
    dpi: int = DPI,
    linestyle: str = LINESTYLE,
    linewidth: float = LINEWIDTH,
    padding: float = PADDING,
):
    """Process a single toolpath file for visualization."""

    # Load geometries from file
    geometries = load_geometries(toolpath_file, binary)

    # Create visualization
    _, ax = plt.subplots(figsize=(10, 10))

    # Plot geometries
    plot_geometries(ax, geometries, color, linewidth, alpha, linestyle)

    # Set consistent bounds across all layers using mesh bounds with padding
    set_axis_bounds(ax, mesh_bounds, padding)

    # Set title with layer number
    layer_number = toolpath_file.stem
    ax.set_title(f"Toolpath (Layer {layer_number})")

    # Save image with same base name as data file
    image_file = toolpath_file.stem + ".png"
    plt.savefig(images_out_path / image_file, dpi=dpi)
    plt.close()

    return toolpath_file.name


def compile_gif(images_path: Path, out_path: Path) -> Path:
    """
    Compiles generated images to .gif
    """
    # Compile images into GIF
    image_files = sorted(images_path.glob("*.png"))
    if image_files:
        # Load images into memory and close file handles
        images = []
        for img_file in tqdm(image_files, desc=f"Compiling {out_path.stem}.gif"):
            with Image.open(img_file) as img:
                images.append(img.copy())
        console = Console()
        with console.status(
            f"[bold green]Writing {out_path.stem}.gif...", spinner="dots"
        ):
            images[0].save(
                out_path,
                save_all=True,
                append_images=images[1:],
                duration=200,
                loop=0,
            )
        console.print(
            f"[bold green]✓[/bold green] GIF created: {out_path} ({len(images)} frames)"
        )

    return out_path
