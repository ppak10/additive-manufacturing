import pytest
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from pint import Quantity
from matplotlib.colors import LinearSegmentedColormap

from am.config import BuildParameters
from am.solver.types import MeltPoolDimensions
from am.process_map.models import (
    MeltPoolClassifications,
    ProcessMapPoint,
    ProcessMapPlotData,
)
from am.process_map.plot import get_colormap_segment, plot_process_map


# -------------------------------
# Helper functions
# -------------------------------


def create_test_point(
    beam_power: float = 200.0,
    scan_velocity: float = 0.8,
    lack_of_fusion: bool = False,
) -> ProcessMapPoint:
    """Create a test ProcessMapPoint with given parameters."""
    build_params = BuildParameters(
        beam_power=Quantity(beam_power, "watt"),
        scan_velocity=Quantity(scan_velocity, "meter / second"),
    )
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100.0, "micrometer"),
        width=Quantity(80.0, "micrometer"),
        length=Quantity(150.0, "micrometer"),
        length_front=Quantity(60.0, "micrometer"),
        length_behind=Quantity(90.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(lack_of_fusion=lack_of_fusion)

    return ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )


def create_2d_plot_data() -> ProcessMapPlotData:
    """Create a 2D ProcessMapPlotData for testing."""
    beam_powers = [Quantity(200.0, "watt"), Quantity(250.0, "watt")]
    scan_velocities = [
        Quantity(0.8, "meter / second"),
        Quantity(1.0, "meter / second"),
    ]

    grid = np.empty((2, 2), dtype=object)
    for i, power in enumerate([200.0, 250.0]):
        for j, velocity in enumerate([0.8, 1.0]):
            grid[i, j] = create_test_point(
                beam_power=power,
                scan_velocity=velocity,
                lack_of_fusion=(i + j) % 2 == 0,
            )

    return ProcessMapPlotData(
        parameters=["beam_power", "scan_velocity"],
        axes=[beam_powers, scan_velocities],
        grid=grid,
    )


def create_3d_plot_data() -> ProcessMapPlotData:
    """Create a 3D ProcessMapPlotData for testing."""
    beam_powers = [Quantity(200.0, "watt"), Quantity(250.0, "watt")]
    scan_velocities = [
        Quantity(0.8, "meter / second"),
        Quantity(1.0, "meter / second"),
    ]
    hatch_spacings = [Quantity(40.0, "micrometer"), Quantity(50.0, "micrometer")]

    grid = np.empty((2, 2, 2), dtype=object)
    for i, power in enumerate([200.0, 250.0]):
        for j, velocity in enumerate([0.8, 1.0]):
            for k, hatch in enumerate([40.0, 50.0]):
                build_params = BuildParameters(
                    beam_power=Quantity(power, "watt"),
                    scan_velocity=Quantity(velocity, "meter / second"),
                    hatch_spacing=Quantity(hatch, "micrometer"),
                )
                melt_pool_dims = MeltPoolDimensions(
                    depth=Quantity(100.0, "micrometer"),
                    width=Quantity(80.0, "micrometer"),
                    length=Quantity(150.0, "micrometer"),
                    length_front=Quantity(60.0, "micrometer"),
                    length_behind=Quantity(90.0, "micrometer"),
                )
                classifications = MeltPoolClassifications(
                    lack_of_fusion=(i + j + k) % 2 == 0
                )
                grid[i, j, k] = ProcessMapPoint(
                    build_parameters=build_params,
                    melt_pool_dimensions=melt_pool_dims,
                    melt_pool_classifications=classifications,
                )

    return ProcessMapPlotData(
        parameters=["beam_power", "scan_velocity", "hatch_spacing"],
        axes=[beam_powers, scan_velocities, hatch_spacings],
        grid=grid,
    )


# -------------------------------
# get_colormap_segment tests
# -------------------------------


def test_get_colormap_segment_returns_colormap():
    """Test that get_colormap_segment returns a LinearSegmentedColormap."""
    base_cmap = plt.get_cmap("plasma")
    position = 0.5
    result = get_colormap_segment(position, base_cmap)

    assert isinstance(result, LinearSegmentedColormap)


def test_get_colormap_segment_at_start():
    """Test get_colormap_segment at position 0."""
    base_cmap = plt.get_cmap("viridis")
    position = 0.0
    result = get_colormap_segment(position, base_cmap)

    assert isinstance(result, LinearSegmentedColormap)


def test_get_colormap_segment_at_end():
    """Test get_colormap_segment at position 1."""
    base_cmap = plt.get_cmap("viridis")
    position = 1.0
    result = get_colormap_segment(position, base_cmap)

    assert isinstance(result, LinearSegmentedColormap)


# -------------------------------
# plot_process_map 2D tests
# -------------------------------


def test_plot_process_map_2d_basic(tmp_path):
    """Test basic 2D plot generation."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


def test_plot_process_map_2d_custom_figsize(tmp_path):
    """Test 2D plot with custom figure size."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
        figsize=(6, 4),
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


def test_plot_process_map_2d_custom_dpi(tmp_path):
    """Test 2D plot with custom DPI."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
        dpi=300,
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


def test_plot_process_map_2d_transparent_background(tmp_path):
    """Test 2D plot with transparent background."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
        transparent_bg=True,
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


# -------------------------------
# plot_process_map 3D tests
# -------------------------------


def test_plot_process_map_3d_basic(tmp_path):
    """Test basic 3D plot generation (layered 2D plots)."""
    plot_data = create_3d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


def test_plot_process_map_3d_custom_settings(tmp_path):
    """Test 3D plot with custom settings."""
    plot_data = create_3d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
        figsize=(8, 6),
        dpi=300,
        transparent_bg=True,
    )

    plot_file = plots_dir / "lack_of_fusion.png"
    assert plot_file.exists()


# -------------------------------
# File output tests
# -------------------------------


def test_plot_process_map_file_is_valid_image(tmp_path):
    """Test that generated file is a valid PNG image."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
    )

    plot_file = plots_dir / "lack_of_fusion.png"

    # Read file header to verify it's a PNG
    with open(plot_file, "rb") as f:
        header = f.read(8)
        # PNG magic number
        assert header == b"\x89PNG\r\n\x1a\n"


# -------------------------------
# Matplotlib cleanup tests
# -------------------------------


def test_plot_process_map_closes_figure(tmp_path):
    """Test that plotting properly closes matplotlib figure."""
    plot_data = create_2d_plot_data()
    plots_dir = tmp_path / "plots"
    plots_dir.mkdir()

    initial_fig_count = len(plt.get_fignums())

    plot_process_map(
        process_map_path=tmp_path,
        plot_data=plot_data,
        plot_type="lack_of_fusion",
    )

    final_fig_count = len(plt.get_fignums())
    assert final_fig_count == initial_fig_count
