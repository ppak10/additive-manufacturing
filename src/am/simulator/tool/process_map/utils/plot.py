from matplotlib.colors import LinearSegmentedColormap


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
