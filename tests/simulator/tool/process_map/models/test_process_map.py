import pytest
import json
import tempfile
from pathlib import Path

from am.simulator.tool.process_map.models.process_map import ProcessMap
from am.simulator.tool.process_map.models.process_map_parameter_range import (
    ProcessMapParameterRange,
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
def process_map_parameter_ranges():
    """Create a list of ProcessMapParameterRange fixtures."""
    return [
        ProcessMapParameterRange(name="beam_power"),
        ProcessMapParameterRange(name="scan_velocity"),
    ]


@pytest.fixture
def process_map(build_parameters, material, process_map_parameter_ranges, temp_dir):
    """Create a ProcessMap fixture."""
    return ProcessMap(
        build_parameters=build_parameters,
        material=material,
        parameter_ranges=process_map_parameter_ranges,
        out_path=temp_dir,
    )


class TestProcessMapCreation:
    """Test ProcessMap creation and initialization."""

    def test_create_process_map_with_defaults(
        self, build_parameters, material, temp_dir
    ):
        """Test creating a ProcessMap with default parameters."""
        param_range = ProcessMapParameterRange(name="beam_power")
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=[param_range],
            out_path=temp_dir,
        )

        assert process_map.build_parameters is not None
        assert process_map.material is not None
        assert len(process_map.parameter_ranges) == 1
        assert process_map.parameter_ranges[0].name == "beam_power"
        assert process_map.out_path == temp_dir

    def test_create_process_map_with_multiple_parameters(
        self, build_parameters, material, temp_dir
    ):
        """Test creating a ProcessMap with multiple parameters."""
        param_ranges = [
            ProcessMapParameterRange(name="beam_power"),
            ProcessMapParameterRange(name="scan_velocity"),
            ProcessMapParameterRange(name="layer_height"),
        ]
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=param_ranges,
            out_path=temp_dir,
        )

        assert len(process_map.parameter_ranges) == 3
        assert process_map.parameter_ranges[0].name == "beam_power"
        assert process_map.parameter_ranges[1].name == "scan_velocity"
        assert process_map.parameter_ranges[2].name == "layer_height"

    def test_create_process_map_with_empty_parameters(
        self, build_parameters, material, temp_dir
    ):
        """Test creating a ProcessMap with empty parameters list."""
        process_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=[],
            out_path=temp_dir,
        )

        assert len(process_map.parameter_ranges) == 0

    def test_create_process_map_with_custom_build_params(self, material, temp_dir):
        """Test creating a ProcessMap with custom build parameters."""
        custom_build_params = BuildParameters(
            beam_power=(300, "watts"), scan_velocity=(1.0, "meter / second")
        )
        param_range = ProcessMapParameterRange(name="beam_power")
        process_map = ProcessMap(
            build_parameters=custom_build_params,
            material=material,
            parameter_ranges=[param_range],
            out_path=temp_dir,
        )

        assert process_map.build_parameters.beam_power.magnitude == 300
        assert process_map.build_parameters.scan_velocity.magnitude == 1.0


class TestProcessMapSave:
    """Test ProcessMap save functionality."""

    def test_save_default_path(self, process_map):
        """Test saving ProcessMap to default path."""
        saved_path = process_map.save()

        assert saved_path.exists()
        assert saved_path.name == "process_map.json"
        assert saved_path.parent == process_map.out_path

    def test_save_custom_path(self, process_map, temp_dir):
        """Test saving ProcessMap to custom path."""
        custom_path = temp_dir / "custom_process_map.json"
        saved_path = process_map.save(file_path=custom_path)

        assert saved_path.exists()
        assert saved_path == custom_path

    def test_save_creates_valid_json(self, process_map):
        """Test that saved file contains valid JSON."""
        saved_path = process_map.save()

        with open(saved_path, "r") as f:
            data = json.load(f)

        assert "build_parameters" in data
        assert "material" in data
        assert "parameter_ranges" in data
        assert "out_path" in data

    def test_save_preserves_parameter_data(self, process_map):
        """Test that saved file preserves all parameter data."""
        saved_path = process_map.save()

        with open(saved_path, "r") as f:
            data = json.load(f)

        assert len(data["parameter_ranges"]) == len(process_map.parameter_ranges)
        assert data["parameter_ranges"][0]["name"] == "beam_power"
        assert data["parameter_ranges"][1]["name"] == "scan_velocity"

    def test_save_returns_path(self, process_map):
        """Test that save method returns the saved path."""
        saved_path = process_map.save()

        assert isinstance(saved_path, Path)
        assert saved_path.exists()


class TestProcessMapLoad:
    """Test ProcessMap load functionality."""

    def test_load_from_saved_file(self, process_map, temp_dir):
        """Test loading a ProcessMap from a saved file."""
        saved_path = process_map.save()
        loaded_map = ProcessMap.load(saved_path)

        assert loaded_map.out_path == process_map.out_path
        assert len(loaded_map.parameter_ranges) == len(process_map.parameter_ranges)
        assert (
            loaded_map.parameter_ranges[0].name == process_map.parameter_ranges[0].name
        )

    def test_load_preserves_build_parameters(self, process_map):
        """Test that loading preserves build parameters."""
        saved_path = process_map.save()
        loaded_map = ProcessMap.load(saved_path)

        assert (
            loaded_map.build_parameters.beam_power.magnitude
            == process_map.build_parameters.beam_power.magnitude
        )
        assert (
            loaded_map.build_parameters.scan_velocity.magnitude
            == process_map.build_parameters.scan_velocity.magnitude
        )

    def test_load_preserves_material(self, process_map):
        """Test that loading preserves material properties."""
        saved_path = process_map.save()
        loaded_map = ProcessMap.load(saved_path)

        assert (
            loaded_map.material.density.magnitude
            == process_map.material.density.magnitude
        )
        assert (
            loaded_map.material.thermal_conductivity.magnitude
            == process_map.material.thermal_conductivity.magnitude
        )

    def test_load_preserves_parameter_ranges(self, process_map):
        """Test that loading preserves all parameter ranges."""
        saved_path = process_map.save()
        loaded_map = ProcessMap.load(saved_path)

        assert len(loaded_map.parameter_ranges) == len(process_map.parameter_ranges)
        for i, param_range in enumerate(loaded_map.parameter_ranges):
            assert param_range.name == process_map.parameter_ranges[i].name
            assert (
                param_range.start.magnitude
                == process_map.parameter_ranges[i].start.magnitude
            )
            assert (
                param_range.stop.magnitude
                == process_map.parameter_ranges[i].stop.magnitude
            )
            assert (
                param_range.step.magnitude
                == process_map.parameter_ranges[i].step.magnitude
            )

    def test_load_converts_path_correctly(self, process_map):
        """Test that loading converts out_path string back to Path."""
        saved_path = process_map.save()
        loaded_map = ProcessMap.load(saved_path)

        assert isinstance(loaded_map.out_path, Path)
        assert loaded_map.out_path == process_map.out_path

    def test_load_nonexistent_file_raises_error(self, temp_dir):
        """Test that loading from nonexistent file raises error."""
        nonexistent_path = temp_dir / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            ProcessMap.load(nonexistent_path)


class TestProcessMapSaveLoadRoundTrip:
    """Test save/load round-trip consistency."""

    def test_round_trip_preserves_all_data(self, build_parameters, material, temp_dir):
        """Test that saving and loading preserves all data."""
        original_param_ranges = [
            ProcessMapParameterRange(
                name="beam_power",
                start=(150, "watts"),
                stop=(900, "watts"),
                step=(50, "watts"),
            ),
            ProcessMapParameterRange(name="scan_velocity"),
            ProcessMapParameterRange(name="layer_height"),
        ]

        original_map = ProcessMap(
            build_parameters=build_parameters,
            material=material,
            parameter_ranges=original_param_ranges,
            out_path=temp_dir,
        )

        saved_path = original_map.save()
        loaded_map = ProcessMap.load(saved_path)

        # Check build parameters
        assert (
            loaded_map.build_parameters.beam_power.magnitude
            == original_map.build_parameters.beam_power.magnitude
        )

        # Check material
        assert (
            loaded_map.material.density.magnitude
            == original_map.material.density.magnitude
        )

        # Check parameter ranges
        assert len(loaded_map.parameter_ranges) == len(original_map.parameter_ranges)
        for i in range(len(original_param_ranges)):
            assert (
                loaded_map.parameter_ranges[i].name
                == original_map.parameter_ranges[i].name
            )
            assert (
                loaded_map.parameter_ranges[i].start.magnitude
                == original_map.parameter_ranges[i].start.magnitude
            )

        # Check path
        assert loaded_map.out_path == original_map.out_path

    def test_multiple_save_load_cycles(self, process_map, temp_dir):
        """Test multiple save/load cycles maintain data integrity."""
        path1 = temp_dir / "cycle1.json"
        path2 = temp_dir / "cycle2.json"
        path3 = temp_dir / "cycle3.json"

        # First cycle
        process_map.save(file_path=path1)
        loaded1 = ProcessMap.load(path1)

        # Second cycle
        loaded1.save(file_path=path2)
        loaded2 = ProcessMap.load(path2)

        # Third cycle
        loaded2.save(file_path=path3)
        loaded3 = ProcessMap.load(path3)

        # Verify data integrity after multiple cycles
        assert loaded3.parameter_ranges[0].name == process_map.parameter_ranges[0].name
        assert (
            loaded3.parameter_ranges[0].start.magnitude
            == process_map.parameter_ranges[0].start.magnitude
        )
        assert (
            loaded3.build_parameters.beam_power.magnitude
            == process_map.build_parameters.beam_power.magnitude
        )


class TestProcessMapValidation:
    """Test ProcessMap validation and edge cases."""

    def test_missing_build_parameters_raises_error(self, material, temp_dir):
        """Test that missing build_parameters raises validation error."""
        with pytest.raises(Exception):
            ProcessMap(material=material, parameter_ranges=[], out_path=temp_dir)

    def test_missing_material_raises_error(self, build_parameters, temp_dir):
        """Test that missing material raises validation error."""
        with pytest.raises(Exception):
            ProcessMap(
                build_parameters=build_parameters,
                parameter_ranges=[],
                out_path=temp_dir,
            )

    def test_missing_parameter_ranges_raises_error(
        self, build_parameters, material, temp_dir
    ):
        """Test that missing parameter_ranges raises validation error."""
        with pytest.raises(Exception):
            ProcessMap(
                build_parameters=build_parameters, material=material, out_path=temp_dir
            )

    def test_missing_out_path_raises_error(self, build_parameters, material):
        """Test that missing out_path raises validation error."""
        with pytest.raises(Exception):
            ProcessMap(
                build_parameters=build_parameters,
                material=material,
                parameter_ranges=[],
            )

    def test_invalid_parameter_range_type_raises_error(
        self, build_parameters, material, temp_dir
    ):
        """Test that invalid parameter range type raises validation error."""
        with pytest.raises(Exception):
            ProcessMap(
                build_parameters=build_parameters,
                material=material,
                parameter_ranges=["not_a_parameter_range"],
                out_path=temp_dir,
            )
