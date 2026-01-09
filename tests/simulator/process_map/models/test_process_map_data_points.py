import pytest
import json
import tempfile
from pathlib import Path

from am.simulator.tool.process_map.models.process_map import ProcessMap
from am.simulator.tool.process_map.models.process_map_parameter_range import (
    ProcessMapParameterRange,
)
from am.simulator.tool.process_map.models.process_map_data_point import (
    ProcessMapDataPoint,
)
from am.config import BuildParameters, Material


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def build_parameters():
    """Create a BuildParameters fixture with default values."""
    return BuildParameters()


@pytest.fixture
def material():
    """Create a Material fixture with default values."""
    return Material()


@pytest.fixture
def single_param_ranges():
    """Create a single parameter range for testing."""
    return [
        ProcessMapParameterRange(
            name="beam_power",
            start=(100, "watts"),
            stop=(300, "watts"),
            step=(100, "watts"),
        )
    ]


@pytest.fixture
def two_param_ranges():
    """Create two parameter ranges for testing."""
    return [
        ProcessMapParameterRange(
            name="beam_power",
            start=(100, "watts"),
            stop=(200, "watts"),
            step=(100, "watts"),
        ),
        ProcessMapParameterRange(
            name="scan_velocity",
            start=(100, "millimeter / second"),
            stop=(200, "millimeter / second"),
            step=(100, "millimeter / second"),
        ),
    ]


@pytest.fixture
def three_param_ranges():
    """Create three parameter ranges for testing."""
    return [
        ProcessMapParameterRange(
            name="beam_power",
            start=(100, "watts"),
            stop=(200, "watts"),
            step=(100, "watts"),
        ),
        ProcessMapParameterRange(
            name="scan_velocity",
            start=(100, "millimeter / second"),
            stop=(200, "millimeter / second"),
            step=(100, "millimeter / second"),
        ),
        ProcessMapParameterRange(
            name="layer_height",
            start=(25, "microns"),
            stop=(50, "microns"),
            step=(25, "microns"),
        ),
    ]


class TestDataPointsGeneration:
    """Test automatic generation of data_points from parameter_ranges."""

    def test_data_points_generated_on_access(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data_points are generated when first accessed."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        # Access data_points - should trigger generation
        data_points = process_map.data_points

        assert data_points is not None
        assert isinstance(data_points, list)
        assert len(data_points) > 0

    def test_single_parameter_generates_correct_count(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that single parameter generates correct number of data points."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # Range: 100 to 300, step 100 = [100, 200, 300] = 3 points
        assert len(data_points) == 3

    def test_two_parameters_generate_cartesian_product(
        self, build_parameters, material, two_param_ranges, temp_dir
    ):
        """Test that two parameters generate correct cartesian product."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=two_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # beam_power: [100, 200] = 2 points
        # scan_velocity: [100, 200] = 2 points
        # Cartesian product: 2 * 2 = 4 points
        assert len(data_points) == 4

    def test_three_parameters_generate_cartesian_product(
        self, build_parameters, material, three_param_ranges, temp_dir
    ):
        """Test that three parameters generate correct cartesian product."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=three_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # beam_power: [100, 200] = 2 points
        # scan_velocity: [100, 200] = 2 points
        # layer_height: [25, 50] = 2 points
        # Cartesian product: 2 * 2 * 2 = 8 points
        assert len(data_points) == 8

    def test_data_points_are_process_map_data_point_objects(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that generated data_points are ProcessMapDataPoint instances."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        for data_point in data_points:
            assert isinstance(data_point, ProcessMapDataPoint)

    def test_data_point_has_correct_structure(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that each data point has correct structure."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        for data_point in data_points:
            assert hasattr(data_point, "parameters")
            assert hasattr(data_point, "melt_pool_dimensions")
            assert hasattr(data_point, "labels")
            assert isinstance(data_point.parameters, list)
            assert data_point.melt_pool_dimensions is None
            assert data_point.labels is None

    def test_data_point_parameters_have_correct_names(
        self, build_parameters, material, two_param_ranges, temp_dir
    ):
        """Test that data point parameters have correct names."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=two_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        for data_point in data_points:
            assert len(data_point.parameters) == 2
            assert data_point.parameters[0].name == "beam_power"
            assert data_point.parameters[1].name == "scan_velocity"

    def test_data_point_parameters_have_correct_values(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data point parameters have correct values."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # Expected values: [100, 200, 300]
        expected_values = [100, 200, 300]

        for i, data_point in enumerate(data_points):
            assert len(data_point.parameters) == 1
            param = data_point.parameters[0]
            assert param.value.magnitude == expected_values[i]
            assert str(param.value.units) == "watt"

    def test_data_point_parameters_include_all_combinations(
        self, build_parameters, material, two_param_ranges, temp_dir
    ):
        """Test that all parameter combinations are present."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=two_param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # Expected combinations:
        # (100W, 100mm/s), (100W, 200mm/s), (200W, 100mm/s), (200W, 200mm/s)
        expected_combinations = [
            (100, 100),
            (100, 200),
            (200, 100),
            (200, 200),
        ]

        actual_combinations = [
            (
                dp.parameters[0].value.magnitude,
                dp.parameters[1].value.magnitude,
            )
            for dp in data_points
        ]

        assert actual_combinations == expected_combinations

    def test_empty_parameter_ranges_generates_single_empty_point(
        self, build_parameters, material, temp_dir
    ):
        """Test that empty parameter ranges generates single empty data point."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=[],
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # With no parameter ranges, should get 1 data point with no parameters
        assert len(data_points) == 1
        assert len(data_points[0].parameters) == 0


class TestDataPointsCaching:
    """Test that data_points are cached after first generation."""

    def test_data_points_cached_after_first_access(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that accessing data_points multiple times returns same object."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        # Access data_points twice
        data_points_1 = process_map.data_points
        data_points_2 = process_map.data_points

        # Should be the same object (cached)
        assert data_points_1 is data_points_2

    def test_private_data_points_field_set_after_generation(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that _data_points private field is set after generation."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        # Initially should be None
        assert process_map._data_points is None

        # Access data_points to trigger generation
        _ = process_map.data_points

        # Now _data_points should be set
        assert process_map._data_points is not None
        assert isinstance(process_map._data_points, list)


class TestDataPointsSaveLoad:
    """Test that data_points are properly saved and loaded."""

    def test_data_points_included_in_save(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data_points are included when saving."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        # Access data_points to ensure they're generated
        _ = process_map.data_points

        # Save to file
        saved_path = process_map.save()

        # Load JSON and verify data_points are present
        with open(saved_path, "r") as f:
            data = json.load(f)

        assert "data_points" in data
        assert isinstance(data["data_points"], list)
        assert len(data["data_points"]) == 3

    def test_data_points_loaded_from_file(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data_points are loaded when loading ProcessMap."""
        # Create and save
        original_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )
        _ = original_map.data_points  # Generate data points
        saved_path = original_map.save()

        # Load
        loaded_map = ProcessMap.load(saved_path)

        # Verify data_points are loaded
        assert loaded_map.data_points is not None
        assert len(loaded_map.data_points) == len(original_map.data_points)

    def test_loaded_data_points_have_same_values(
        self, build_parameters, material, two_param_ranges, temp_dir
    ):
        """Test that loaded data_points have same values as original."""
        # Create and save
        original_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=two_param_ranges,
            out_path=temp_dir,
        )
        original_data_points = original_map.data_points
        saved_path = original_map.save()

        # Load
        loaded_map = ProcessMap.load(saved_path)
        loaded_data_points = loaded_map.data_points

        # Verify same number of points
        assert len(loaded_data_points) == len(original_data_points)

        # Verify each data point has same values
        for orig_dp, loaded_dp in zip(original_data_points, loaded_data_points):
            assert len(loaded_dp.parameters) == len(orig_dp.parameters)
            for orig_param, loaded_param in zip(
                orig_dp.parameters, loaded_dp.parameters
            ):
                assert loaded_param.name == orig_param.name
                assert loaded_param.value.magnitude == orig_param.value.magnitude
                assert str(loaded_param.value.units) == str(orig_param.value.units)

    def test_loaded_data_points_use_cache(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that loaded data_points use cache instead of regenerating."""
        # Create and save
        original_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )
        _ = original_map.data_points
        saved_path = original_map.save()

        # Load
        loaded_map = ProcessMap.load(saved_path)

        # _data_points should be set from loading
        assert loaded_map._data_points is not None

        # Accessing data_points should return cached version
        data_points_1 = loaded_map.data_points
        data_points_2 = loaded_map.data_points

        assert data_points_1 is data_points_2

    def test_save_load_preserves_data_point_structure(
        self, build_parameters, material, three_param_ranges, temp_dir
    ):
        """Test that save/load preserves complete data point structure."""
        # Create and save
        original_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=three_param_ranges,
            out_path=temp_dir,
        )
        _ = original_map.data_points
        saved_path = original_map.save()

        # Load
        loaded_map = ProcessMap.load(saved_path)

        # Verify structure is preserved
        for dp in loaded_map.data_points:
            assert isinstance(dp, ProcessMapDataPoint)
            assert hasattr(dp, "parameters")
            assert hasattr(dp, "melt_pool_dimensions")
            assert hasattr(dp, "labels")
            assert len(dp.parameters) == 3


class TestDataPointsWithCustomRanges:
    """Test data_points generation with custom parameter ranges."""

    def test_fractional_step_generates_correct_points(
        self, build_parameters, material, temp_dir
    ):
        """Test that fractional steps generate correct number of points."""
        param_ranges = [
            ProcessMapParameterRange(
                name="beam_power",
                start=(100, "watts"),
                stop=(150, "watts"),
                step=(25, "watts"),
            )
        ]

        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # Range: 100 to 150, step 25 = [100, 125, 150] = 3 points
        assert len(data_points) == 3

        values = [dp.parameters[0].value.magnitude for dp in data_points]
        assert values == [100, 125, 150]

    def test_large_parameter_space(self, build_parameters, material, temp_dir):
        """Test generation with larger parameter space."""
        param_ranges = [
            ProcessMapParameterRange(
                name="beam_power",
                start=(100, "watts"),
                stop=(500, "watts"),
                step=(100, "watts"),
            ),
            ProcessMapParameterRange(
                name="scan_velocity",
                start=(100, "millimeter / second"),
                stop=(300, "millimeter / second"),
                step=(100, "millimeter / second"),
            ),
        ]

        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # beam_power: [100, 200, 300, 400, 500] = 5 points
        # scan_velocity: [100, 200, 300] = 3 points
        # Total: 5 * 3 = 15 points
        assert len(data_points) == 15

    def test_single_value_range(self, build_parameters, material, temp_dir):
        """Test parameter range with single value (start == stop)."""
        param_ranges = [
            ProcessMapParameterRange(
                name="beam_power",
                start=(100, "watts"),
                stop=(100, "watts"),
                step=(100, "watts"),
            )
        ]

        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=param_ranges,
            out_path=temp_dir,
        )

        data_points = process_map.data_points

        # Should generate exactly 1 point
        assert len(data_points) == 1
        assert data_points[0].parameters[0].value.magnitude == 100


class TestDataPointsReadOnly:
    """Test that data_points is read-only and cannot be set directly."""

    def test_cannot_set_data_points_directly(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data_points cannot be set by user."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
        )

        # Attempting to set data_points should fail (computed property)
        with pytest.raises(AttributeError):
            process_map.data_points = []

    def test_data_points_ignored_if_passed_to_init(
        self, build_parameters, material, single_param_ranges, temp_dir
    ):
        """Test that data_points passed to __init__ are ignored and computed instead."""
        # Create some dummy data points
        dummy_data_points = []

        # Attempting to pass data_points to init - Pydantic allows but ignores
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=single_param_ranges,
            out_path=temp_dir,
            data_points=dummy_data_points,  # This should be ignored
        )

        # data_points should be computed from parameter_ranges, not use dummy
        assert len(process_map.data_points) == 3  # Not 0 from dummy_data_points
        assert process_map.data_points != dummy_data_points
