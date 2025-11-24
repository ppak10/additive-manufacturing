import pytest
import json
from pathlib import Path
from pint import Quantity
from unittest.mock import Mock, patch

from am.config import BuildParameters, Material, ProcessMap
from am.solver.types import MeltPoolDimensions
from am.process_map.run import run_process_map_point, run_process_map
from am.process_map.models import ProcessMapPoint, ProcessMapPoints


# -------------------------------
# run_process_map_point tests
# -------------------------------


def test_run_process_map_point_basic():
    """Test basic execution of run_process_map_point."""
    build_parameters = BuildParameters()
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Verify result is a ProcessMapPoint
    assert isinstance(result, ProcessMapPoint)
    assert result.build_parameters is not None
    assert result.melt_pool_dimensions is not None
    assert result.melt_pool_classifications is not None


def test_run_process_map_point_with_custom_parameters():
    """Test run_process_map_point with custom build parameters."""
    build_parameters = BuildParameters(
        beam_power=Quantity(250.0, "watt"),
        scan_velocity=Quantity(1.0, "meter / second"),
    )
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Verify parameters are preserved
    assert result.build_parameters.beam_power.magnitude == 250.0
    assert result.build_parameters.scan_velocity.magnitude == 1.0


def test_run_process_map_point_returns_melt_pool_dimensions():
    """Test that run_process_map_point returns valid melt pool dimensions."""
    build_parameters = BuildParameters()
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Verify melt pool dimensions exist and have expected fields
    assert hasattr(result.melt_pool_dimensions, "depth")
    assert hasattr(result.melt_pool_dimensions, "width")
    assert hasattr(result.melt_pool_dimensions, "length")

    # Verify dimensions are positive
    assert result.melt_pool_dimensions.depth.magnitude > 0
    assert result.melt_pool_dimensions.width.magnitude > 0
    assert result.melt_pool_dimensions.length.magnitude > 0


def test_run_process_map_point_calculates_lack_of_fusion():
    """Test that run_process_map_point calculates lack_of_fusion classification."""
    build_parameters = BuildParameters(
        hatch_spacing=Quantity(50.0, "micrometer"),
        layer_height=Quantity(100.0, "micrometer"),
    )
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Verify classification exists and is a boolean
    assert result.melt_pool_classifications.lack_of_fusion is not None
    assert isinstance(result.melt_pool_classifications.lack_of_fusion, bool)


def test_run_process_map_point_with_high_power():
    """Test run_process_map_point with high beam power."""
    build_parameters = BuildParameters(
        beam_power=Quantity(400.0, "watt"),
    )
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Higher power should generally result in larger melt pool
    assert result.melt_pool_dimensions.depth.magnitude > 0
    assert isinstance(result, ProcessMapPoint)


def test_run_process_map_point_with_low_power():
    """Test run_process_map_point with low beam power."""
    build_parameters = BuildParameters(
        beam_power=Quantity(100.0, "watt"),
    )
    material = Material()

    result = run_process_map_point(build_parameters, material)

    # Should still produce valid result
    assert result.melt_pool_dimensions.depth.magnitude > 0
    assert isinstance(result, ProcessMapPoint)


def test_run_process_map_point_with_different_materials():
    """Test run_process_map_point with different material properties."""
    build_parameters = BuildParameters()

    # Material with higher thermal conductivity
    material_high_k = Material(
        thermal_conductivity=Quantity(15.0, "watt / (meter * kelvin)"),
    )

    # Material with lower thermal conductivity
    material_low_k = Material(
        thermal_conductivity=Quantity(5.0, "watt / (meter * kelvin)"),
    )

    result_high_k = run_process_map_point(build_parameters, material_high_k)
    result_low_k = run_process_map_point(build_parameters, material_low_k)

    # Both should produce valid results
    assert isinstance(result_high_k, ProcessMapPoint)
    assert isinstance(result_low_k, ProcessMapPoint)


# -------------------------------
# run_process_map single process tests
# -------------------------------


def test_run_process_map_single_process_basic(tmp_path):
    """Test run_process_map with single process (num_proc=1)."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify result is ProcessMapPoints
    assert isinstance(result, ProcessMapPoints)
    assert len(result.points) > 0


def test_run_process_map_single_process_saves_file(tmp_path):
    """Test that run_process_map saves points.json file."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify points.json was created
    points_file = tmp_path / "points.json"
    assert points_file.exists()

    # Verify file can be loaded
    loaded = ProcessMapPoints.load(points_file)
    assert isinstance(loaded, ProcessMapPoints)


def test_run_process_map_single_parameter(tmp_path):
    """Test run_process_map with single parameter variation."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Should have 3 points: 200, 250, 300
    assert len(result.points) == 3
    assert result.parameters == ["beam_power"]


def test_run_process_map_two_parameters(tmp_path):
    """Test run_process_map with two parameter variations."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(100.0, "watt"),
                )
            },
            {
                "scan_velocity": (
                    Quantity(0.8, "meter / second"),
                    Quantity(1.0, "meter / second"),
                    Quantity(0.2, "meter / second"),
                )
            },
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Should have 2 x 2 = 4 points
    assert len(result.points) == 4
    assert result.parameters == ["beam_power", "scan_velocity"]


def test_run_process_map_preserves_parameters(tmp_path):
    """Test that run_process_map preserves parameter values in results."""
    build_parameters = BuildParameters()
    material = Material()
    beam_powers = [200.0, 250.0, 300.0]
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(beam_powers[0], "watt"),
                    Quantity(beam_powers[-1], "watt"),
                    Quantity(beam_powers[1] - beam_powers[0], "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify each point has the correct beam_power
    result_powers = sorted(
        [point.build_parameters.beam_power.magnitude for point in result.points]
    )
    assert result_powers == beam_powers


def test_run_process_map_includes_classifications(tmp_path):
    """Test that run_process_map includes melt pool classifications."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify all points have classifications
    for point in result.points:
        assert point.melt_pool_classifications is not None
        assert point.melt_pool_classifications.lack_of_fusion is not None


# -------------------------------
# run_process_map multiprocess tests
# -------------------------------


def test_run_process_map_multiprocess_basic(tmp_path):
    """Test run_process_map with multiple processes."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=2,
    )

    # Verify result is valid
    assert isinstance(result, ProcessMapPoints)
    assert len(result.points) > 0


def test_run_process_map_multiprocess_same_results_as_single(tmp_path):
    """Test that multiprocess produces same number of results as single process."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result_single = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path / "single",
        num_proc=1,
    )

    result_multi = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path / "multi",
        num_proc=2,
    )

    # Should have same number of points
    assert len(result_single.points) == len(result_multi.points)


def test_run_process_map_multiprocess_with_many_points(tmp_path):
    """Test multiprocess with larger number of points."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            },
            {
                "scan_velocity": (
                    Quantity(0.6, "meter / second"),
                    Quantity(1.0, "meter / second"),
                    Quantity(0.2, "meter / second"),
                )
            },
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=2,
    )

    # Should have 3 x 3 = 9 points
    assert len(result.points) == 9


# -------------------------------
# Edge cases
# -------------------------------


def test_run_process_map_with_single_point(tmp_path):
    """Test run_process_map with only one point."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(200.0, "watt"),
                    Quantity(1.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    assert len(result.points) == 1


def test_run_process_map_with_num_proc_zero(tmp_path):
    """Test run_process_map with num_proc=0 (should use single process)."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=0,
    )

    # Should still work (treated as single process)
    assert isinstance(result, ProcessMapPoints)
    assert len(result.points) > 0


def test_run_process_map_different_base_parameters(tmp_path):
    """Test that base build_parameters are used when not varied."""
    build_parameters = BuildParameters(
        beam_power=Quantity(200.0, "watt"),
        scan_velocity=Quantity(1.5, "meter / second"),  # This is the base
        hatch_spacing=Quantity(60.0, "micrometer"),
    )
    material = Material()

    # Only vary beam_power, other parameters should use base values
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(250.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # All points should have the base scan_velocity and hatch_spacing
    for point in result.points:
        assert point.build_parameters.scan_velocity.magnitude == 1.5
        assert point.build_parameters.hatch_spacing.magnitude == 60.0


# -------------------------------
# Integration tests
# -------------------------------


def test_run_process_map_full_workflow(tmp_path):
    """Test complete workflow: run process map and load results."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(300.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    # Run process map
    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Save was called automatically, so load it back
    points_file = tmp_path / "points.json"
    loaded = ProcessMapPoints.load(points_file)

    # Verify loaded data matches result
    assert len(loaded.points) == len(result.points)
    assert loaded.parameters == result.parameters


def test_run_process_map_results_have_all_fields(tmp_path):
    """Test that all result points have complete data."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "beam_power": (
                    Quantity(200.0, "watt"),
                    Quantity(250.0, "watt"),
                    Quantity(50.0, "watt"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify each point has all required fields
    for point in result.points:
        # Build parameters
        assert point.build_parameters is not None
        assert point.build_parameters.beam_power is not None

        # Melt pool dimensions
        assert point.melt_pool_dimensions is not None
        assert point.melt_pool_dimensions.depth is not None
        assert point.melt_pool_dimensions.width is not None
        assert point.melt_pool_dimensions.length is not None

        # Classifications
        assert point.melt_pool_classifications is not None
        assert point.melt_pool_classifications.lack_of_fusion is not None


def test_run_process_map_varies_correct_parameter(tmp_path):
    """Test that the correct parameter is varied in results."""
    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameter_ranges=[
            {
                "scan_velocity": (
                    Quantity(0.8, "meter / second"),
                    Quantity(1.2, "meter / second"),
                    Quantity(0.2, "meter / second"),
                )
            }
        ],
    )

    result = run_process_map(
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        process_map_path=tmp_path,
        num_proc=1,
    )

    # Verify scan_velocity varies
    velocities = [
        point.build_parameters.scan_velocity.magnitude for point in result.points
    ]
    assert len(set(velocities)) == 3  # Should have 3 unique values

    # Verify other parameters stay constant
    powers = [point.build_parameters.beam_power.magnitude for point in result.points]
    assert len(set(powers)) == 1  # Should all be the same
