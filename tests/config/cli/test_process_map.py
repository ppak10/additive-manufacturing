import pytest
import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner
from am.config.cli import app
from am.config.process_map import ProcessMap


@pytest.fixture
def runner():
    """Create CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    import json

    temp_dir = Path(tempfile.mkdtemp())
    workspace_path = temp_dir / "test_workspace"
    workspace_path.mkdir()
    (workspace_path / "configs" / "process_maps").mkdir(parents=True)

    # Create workspace.json to make it a valid workspace
    workspace_config = {"name": "test_workspace", "version": "0.1.0"}
    (workspace_path / "workspace.json").write_text(
        json.dumps(workspace_config, indent=2)
    )

    yield workspace_path

    # Cleanup
    shutil.rmtree(temp_dir)


# -------------------------------
# Help and basic tests
# -------------------------------


def test_process_map_help(runner):
    """Test process-map CLI help command."""
    result = runner.invoke(app, ["process-map", "--help"])
    assert result.exit_code == 0
    assert "Create process map configuration file" in result.stdout
    assert "--p1-parameter" in result.stdout
    assert "--p2-parameter" in result.stdout
    assert "--p3-parameter" in result.stdout


# -------------------------------
# Single parameter tests
# -------------------------------


def test_create_process_map_single_parameter(runner, temp_workspace):
    """Test creating process map with single parameter."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "single_param",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "300",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0
    assert "Process map saved" in result.stdout

    # Verify file was created
    save_path = temp_workspace / "configs" / "process_maps" / "single_param.json"
    assert save_path.exists()

    # Load and verify contents
    loaded = ProcessMap.load(save_path)
    assert loaded.parameters == ["beam_power"]
    assert len(loaded.points) == 3  # 100, 200, 300


def test_create_process_map_single_parameter_verbose(runner, temp_workspace):
    """Test creating process map with single parameter in verbose mode."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "verbose_test",
            "--p1-parameter",
            "scan_velocity",
            "--p1-min",
            "0.5",
            "--p1-max",
            "1.5",
            "--p1-step",
            "0.5",
            "--p1-unit",
            "meter/second",
            "--workspace",
            str(temp_workspace),
            "--verbose",
        ],
    )

    assert result.exit_code == 0
    assert "Creating ProcessMap with 1 parameter(s)" in result.stdout
    assert "Generated 3 points from parameter ranges" in result.stdout
    assert "Parameters: ['scan_velocity']" in result.stdout


# -------------------------------
# Two parameter tests
# -------------------------------


def test_create_process_map_two_parameters(runner, temp_workspace):
    """Test creating process map with two parameters (Cartesian product)."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "two_params",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--p2-parameter",
            "scan_velocity",
            "--p2-min",
            "0.5",
            "--p2-max",
            "1.5",
            "--p2-step",
            "0.5",
            "--p2-unit",
            "meter/second",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0

    # Load and verify
    save_path = temp_workspace / "configs" / "process_maps" / "two_params.json"
    loaded = ProcessMap.load(save_path)
    assert loaded.parameters == ["beam_power", "scan_velocity"]
    assert len(loaded.points) == 6  # 2 power × 3 velocity


# -------------------------------
# Three parameter tests
# -------------------------------


def test_create_process_map_three_parameters(runner, temp_workspace):
    """Test creating process map with three parameters (maximum allowed)."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "three_params",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--p2-parameter",
            "scan_velocity",
            "--p2-min",
            "0.5",
            "--p2-max",
            "1.0",
            "--p2-step",
            "0.5",
            "--p2-unit",
            "m/s",
            "--p3-parameter",
            "hatch_spacing",
            "--p3-min",
            "50",
            "--p3-max",
            "100",
            "--p3-step",
            "50",
            "--p3-unit",
            "micrometer",
            "--workspace",
            str(temp_workspace),
            "--verbose",
        ],
    )

    assert result.exit_code == 0

    # Load and verify
    save_path = temp_workspace / "configs" / "process_maps" / "three_params.json"
    loaded = ProcessMap.load(save_path)
    assert loaded.parameters == ["beam_power", "scan_velocity", "hatch_spacing"]
    assert len(loaded.points) == 8  # 2 × 2 × 2


# -------------------------------
# Validation error tests
# -------------------------------


def test_process_map_no_parameters_error(runner, temp_workspace):
    """Test that not providing any parameters returns error."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "no_params",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 1
    assert "At least one parameter must be specified" in result.stdout


def test_process_map_incomplete_parameter_error(runner, temp_workspace):
    """Test that incomplete parameter specification returns error."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "incomplete",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            # Missing --p1-step and --p1-unit
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 1
    assert (
        "For parameter 1, all of --p1-min, --p1-max, --p1-step, and --p1-unit must be"
        in result.stdout
    )


def test_process_map_missing_min_value(runner, temp_workspace):
    """Test error when min value is missing."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--p1-parameter",
            "beam_power",
            # Missing --p1-min
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 1
    assert (
        "For parameter 1, all of --p1-min, --p1-max, --p1-step, and --p1-unit must be"
        in result.stdout
    )


def test_process_map_missing_unit(runner, temp_workspace):
    """Test error when unit is missing."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--p2-parameter",
            "scan_velocity",
            "--p2-min",
            "0.5",
            "--p2-max",
            "1.5",
            "--p2-step",
            "0.5",
            # Missing --p2-unit
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 1
    assert (
        "For parameter 2, all of --p2-min, --p2-max, --p2-step, and --p2-unit must be"
        in result.stdout
    )


def test_process_map_partial_second_parameter(runner, temp_workspace):
    """Test error when second parameter is partially specified."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--p2-parameter",
            "scan_velocity",
            "--p2-min",
            "0.5",
            # Missing p2-max, p2-step, p2-unit
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 1
    assert "For parameter 2" in result.stdout


# -------------------------------
# File content verification tests
# -------------------------------


def test_process_map_file_content_structure(runner, temp_workspace):
    """Test that saved file has correct structure (parameters and points, no parameter_ranges)."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "verify_structure",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0

    # Load and verify structure
    save_path = temp_workspace / "configs" / "process_maps" / "verify_structure.json"
    loaded = ProcessMap.load(save_path)

    # Verify parameter_ranges is not stored
    serialized = loaded.model_dump()
    assert "parameter_ranges" not in serialized
    assert "parameters" in serialized
    assert "points" in serialized


def test_process_map_correct_units(runner, temp_workspace):
    """Test that units are correctly preserved in the saved file."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "unit_test",
            "--p1-parameter",
            "temperature",
            "--p1-min",
            "300",
            "--p1-max",
            "400",
            "--p1-step",
            "50",
            "--p1-unit",
            "kelvin",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0

    save_path = temp_workspace / "configs" / "process_maps" / "unit_test.json"
    loaded = ProcessMap.load(save_path)

    # Check first point has correct units
    assert str(loaded.points[0][0].units) == "kelvin"


# -------------------------------
# Default name tests
# -------------------------------


def test_process_map_default_name(runner, temp_workspace):
    """Test that default name is used when not specified."""
    result = runner.invoke(
        app,
        [
            "process-map",
            # No --name specified
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0

    # Check that default.json was created
    default_path = temp_workspace / "configs" / "process_maps" / "default.json"
    assert default_path.exists()


# -------------------------------
# Round-trip tests
# -------------------------------


def test_process_map_load_and_verify_cartesian_product(runner, temp_workspace):
    """Test that Cartesian product is correctly generated and can be loaded."""
    result = runner.invoke(
        app,
        [
            "process-map",
            "--name",
            "cartesian_test",
            "--p1-parameter",
            "beam_power",
            "--p1-min",
            "100",
            "--p1-max",
            "200",
            "--p1-step",
            "100",
            "--p1-unit",
            "watt",
            "--p2-parameter",
            "scan_velocity",
            "--p2-min",
            "1",
            "--p2-max",
            "2",
            "--p2-step",
            "1",
            "--p2-unit",
            "m/s",
            "--workspace",
            str(temp_workspace),
        ],
    )

    assert result.exit_code == 0

    save_path = temp_workspace / "configs" / "process_maps" / "cartesian_test.json"
    loaded = ProcessMap.load(save_path)

    # Verify all combinations exist
    powers = [100.0, 200.0]
    velocities = [1.0, 2.0]

    assert len(loaded.points) == len(powers) * len(velocities)

    # Check that we have all combinations
    point_tuples = {(p[0].magnitude, p[1].magnitude) for p in loaded.points}
    expected_tuples = {(p, v) for p in powers for v in velocities}
    assert point_tuples == expected_tuples
