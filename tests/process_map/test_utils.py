import pytest
import numpy as np
from pint import Quantity

from am.config import BuildParameters
from am.solver.types import MeltPoolDimensions
from am.process_map.models import (
    MeltPoolClassifications,
    ProcessMapPoint,
    ProcessMapPoints,
)
from am.process_map.utils import process_map_points_to_plot_data


# -------------------------------
# Helper functions
# -------------------------------


def create_test_point(
    beam_power: float = 200.0, scan_velocity: float = 0.8
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
    classifications = MeltPoolClassifications(lack_of_fusion=False)

    return ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )


# -------------------------------
# 1D grid tests (single parameter variation)
# -------------------------------


def test_process_map_points_to_plot_data_1d_grid():
    """Test converting 1D process map points (single parameter varied)."""
    points = []
    beam_powers = [200.0, 250.0, 300.0]

    for power in beam_powers:
        points.append(create_test_point(beam_power=power, scan_velocity=0.8))

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify basic structure
    assert plot_data.parameters == ["beam_power"]
    assert len(plot_data.axes) == 1
    assert len(plot_data.axes[0]) == 3

    # Verify axis values are sorted
    assert plot_data.axes[0][0].magnitude == 200.0
    assert plot_data.axes[0][1].magnitude == 250.0
    assert plot_data.axes[0][2].magnitude == 300.0

    # Verify grid shape
    assert plot_data.grid.shape == (3,)

    # Verify grid contains the points
    assert plot_data.grid[0] is not None
    assert plot_data.grid[0].build_parameters.beam_power.magnitude == 200.0


# -------------------------------
# 2D grid tests (two parameter variations)
# -------------------------------


def test_process_map_points_to_plot_data_2d_grid():
    """Test converting 2D process map points (two parameters varied)."""
    points = []
    beam_powers = [200.0, 250.0, 300.0]
    scan_velocities = [0.6, 0.8, 1.0]

    # Create grid of points
    for power in beam_powers:
        for velocity in scan_velocities:
            points.append(create_test_point(beam_power=power, scan_velocity=velocity))

    process_map_points = ProcessMapPoints(
        parameters=["beam_power", "scan_velocity"], points=points
    )

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify basic structure
    assert plot_data.parameters == ["beam_power", "scan_velocity"]
    assert len(plot_data.axes) == 2

    # Verify axis lengths
    assert len(plot_data.axes[0]) == 3  # beam_power axis
    assert len(plot_data.axes[1]) == 3  # scan_velocity axis

    # Verify axis values are sorted
    assert plot_data.axes[0][0].magnitude == 200.0
    assert plot_data.axes[0][2].magnitude == 300.0
    assert plot_data.axes[1][0].magnitude == 0.6
    assert plot_data.axes[1][2].magnitude == 1.0

    # Verify grid shape (3x3)
    assert plot_data.grid.shape == (3, 3)

    # Verify specific grid points
    assert plot_data.grid[0, 0].build_parameters.beam_power.magnitude == 200.0
    assert plot_data.grid[0, 0].build_parameters.scan_velocity.magnitude == 0.6
    assert plot_data.grid[2, 2].build_parameters.beam_power.magnitude == 300.0
    assert plot_data.grid[2, 2].build_parameters.scan_velocity.magnitude == 1.0


def test_process_map_points_to_plot_data_2d_non_square_grid():
    """Test converting 2D process map with non-square grid."""
    points = []
    beam_powers = [200.0, 250.0]
    scan_velocities = [0.6, 0.8, 1.0, 1.2]

    for power in beam_powers:
        for velocity in scan_velocities:
            points.append(create_test_point(beam_power=power, scan_velocity=velocity))

    process_map_points = ProcessMapPoints(
        parameters=["beam_power", "scan_velocity"], points=points
    )

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify grid shape (2x4)
    assert plot_data.grid.shape == (2, 4)
    assert len(plot_data.axes[0]) == 2
    assert len(plot_data.axes[1]) == 4


# -------------------------------
# 3D grid tests (three parameter variations)
# -------------------------------


def test_process_map_points_to_plot_data_3d_grid():
    """Test converting 3D process map points (three parameters varied)."""
    points = []
    beam_powers = [200.0, 250.0]
    scan_velocities = [0.8, 1.0]
    hatch_spacings = [40.0, 50.0]

    for power in beam_powers:
        for velocity in scan_velocities:
            for hatch in hatch_spacings:
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
                classifications = MeltPoolClassifications(lack_of_fusion=False)
                point = ProcessMapPoint(
                    build_parameters=build_params,
                    melt_pool_dimensions=melt_pool_dims,
                    melt_pool_classifications=classifications,
                )
                points.append(point)

    process_map_points = ProcessMapPoints(
        parameters=["beam_power", "scan_velocity", "hatch_spacing"], points=points
    )

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify basic structure
    assert plot_data.parameters == ["beam_power", "scan_velocity", "hatch_spacing"]
    assert len(plot_data.axes) == 3

    # Verify grid shape (2x2x2)
    assert plot_data.grid.shape == (2, 2, 2)

    # Verify corner points
    assert plot_data.grid[0, 0, 0].build_parameters.beam_power.magnitude == 200.0
    assert plot_data.grid[0, 0, 0].build_parameters.scan_velocity.magnitude == 0.8
    assert plot_data.grid[0, 0, 0].build_parameters.hatch_spacing.magnitude == 40.0

    assert plot_data.grid[1, 1, 1].build_parameters.beam_power.magnitude == 250.0
    assert plot_data.grid[1, 1, 1].build_parameters.scan_velocity.magnitude == 1.0
    assert plot_data.grid[1, 1, 1].build_parameters.hatch_spacing.magnitude == 50.0


# -------------------------------
# Sorting and ordering tests
# -------------------------------


def test_process_map_points_to_plot_data_unsorted_input():
    """Test that function properly sorts unsorted input points."""
    points = []
    # Deliberately create points in random order
    beam_powers = [300.0, 200.0, 250.0]  # Unsorted

    for power in beam_powers:
        points.append(create_test_point(beam_power=power, scan_velocity=0.8))

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify axis values are sorted despite unsorted input
    assert plot_data.axes[0][0].magnitude == 200.0
    assert plot_data.axes[0][1].magnitude == 250.0
    assert plot_data.axes[0][2].magnitude == 300.0


def test_process_map_points_to_plot_data_2d_random_order():
    """Test 2D grid with points added in random order."""
    points = []
    # Add points in non-sequential order
    combinations = [
        (300.0, 1.0),
        (200.0, 0.6),
        (250.0, 0.8),
        (200.0, 1.0),
        (300.0, 0.6),
        (250.0, 0.6),
        (200.0, 0.8),
        (300.0, 0.8),
        (250.0, 1.0),
    ]

    for power, velocity in combinations:
        points.append(create_test_point(beam_power=power, scan_velocity=velocity))

    process_map_points = ProcessMapPoints(
        parameters=["beam_power", "scan_velocity"], points=points
    )

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Grid should still be properly organized
    assert plot_data.grid.shape == (3, 3)
    assert plot_data.grid[0, 0].build_parameters.beam_power.magnitude == 200.0
    assert plot_data.grid[0, 0].build_parameters.scan_velocity.magnitude == 0.6
    assert plot_data.grid[2, 2].build_parameters.beam_power.magnitude == 300.0
    assert plot_data.grid[2, 2].build_parameters.scan_velocity.magnitude == 1.0


# -------------------------------
# Edge cases
# -------------------------------


def test_process_map_points_to_plot_data_single_point():
    """Test with a single point."""
    points = [create_test_point(beam_power=200.0, scan_velocity=0.8)]

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    assert plot_data.grid.shape == (1,)
    assert len(plot_data.axes[0]) == 1
    assert plot_data.grid[0] is not None


def test_process_map_points_to_plot_data_duplicate_parameters():
    """Test behavior with duplicate parameter values (same point multiple times)."""
    points = []
    # Create multiple points with same parameters
    for _ in range(3):
        points.append(create_test_point(beam_power=200.0, scan_velocity=0.8))

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Should only have one unique value in axis
    assert len(plot_data.axes[0]) == 1
    assert plot_data.grid.shape == (1,)


def test_process_map_points_to_plot_data_varying_melt_pool_properties():
    """Test that different melt pool properties are preserved in grid."""
    points = []
    beam_powers = [200.0, 250.0, 300.0]

    for i, power in enumerate(beam_powers):
        build_params = BuildParameters(
            beam_power=Quantity(power, "watt"),
        )
        melt_pool_dims = MeltPoolDimensions(
            depth=Quantity(100.0 + i * 10, "micrometer"),
            width=Quantity(80.0 + i * 5, "micrometer"),
            length=Quantity(150.0 + i * 10, "micrometer"),
            length_front=Quantity(60.0, "micrometer"),
            length_behind=Quantity(90.0, "micrometer"),
        )
        classifications = MeltPoolClassifications(lack_of_fusion=(i % 2 == 0))
        point = ProcessMapPoint(
            build_parameters=build_params,
            melt_pool_dimensions=melt_pool_dims,
            melt_pool_classifications=classifications,
        )
        points.append(point)

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify melt pool properties are preserved
    assert plot_data.grid[0].melt_pool_dimensions.depth.magnitude == 100.0
    assert plot_data.grid[1].melt_pool_dimensions.depth.magnitude == 110.0
    assert plot_data.grid[2].melt_pool_dimensions.depth.magnitude == 120.0

    # Verify classifications are preserved
    assert plot_data.grid[0].melt_pool_classifications.lack_of_fusion is True
    assert plot_data.grid[1].melt_pool_classifications.lack_of_fusion is False
    assert plot_data.grid[2].melt_pool_classifications.lack_of_fusion is True


# -------------------------------
# Parameter indexing tests
# -------------------------------


def test_process_map_points_to_plot_data_axis_dict_consistency():
    """Test that the internal axis dictionary produces correct indexing."""
    points = []
    beam_powers = [180.0, 220.0, 260.0, 300.0]

    for power in beam_powers:
        points.append(create_test_point(beam_power=power, scan_velocity=0.8))

    process_map_points = ProcessMapPoints(parameters=["beam_power"], points=points)

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify each point is at the correct index
    for i, power in enumerate([180.0, 220.0, 260.0, 300.0]):
        assert plot_data.grid[i].build_parameters.beam_power.magnitude == power


def test_process_map_points_to_plot_data_multiple_parameters_indexing():
    """Test correct indexing with multiple parameters."""
    points = []
    beam_powers = [200.0, 250.0]
    scan_velocities = [0.6, 0.8, 1.0]

    for power in beam_powers:
        for velocity in scan_velocities:
            points.append(create_test_point(beam_power=power, scan_velocity=velocity))

    process_map_points = ProcessMapPoints(
        parameters=["beam_power", "scan_velocity"], points=points
    )

    plot_data = process_map_points_to_plot_data(process_map_points)

    # Verify all combinations are correctly indexed
    for i, power in enumerate([200.0, 250.0]):
        for j, velocity in enumerate([0.6, 0.8, 1.0]):
            point = plot_data.grid[i, j]
            assert point.build_parameters.beam_power.magnitude == power
            assert point.build_parameters.scan_velocity.magnitude == velocity


# -------------------------------
# Empty/None handling tests
# -------------------------------


def test_process_map_points_to_plot_data_empty_list():
    """Test with empty points list."""
    process_map_points = ProcessMapPoints(parameters=[], points=[])

    plot_data = process_map_points_to_plot_data(process_map_points)

    assert plot_data.grid.shape == ()
    assert len(plot_data.axes) == 0
