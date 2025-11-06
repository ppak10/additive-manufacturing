import pytest
from pathlib import Path

from am.workspace.configs import initialize_configs
from am.config import BuildParameters, Material, MeshParameters


# -------------------------------
# Basic functionality tests
# -------------------------------


def test_initialize_configs_basic(isolated_workspace):
    """Test creating configs folder with default configurations."""
    configs_path = initialize_configs(isolated_workspace)

    assert configs_path.exists()
    assert configs_path.is_dir()
    assert configs_path == isolated_workspace / "configs"


def test_initialize_configs_creates_subdirectories(isolated_workspace):
    """Test that initialize_configs creates the necessary subdirectories."""
    configs_path = initialize_configs(isolated_workspace)

    # Check that subdirectories exist
    assert (configs_path / "build_parameters").exists()
    assert (configs_path / "materials").exists()
    assert (configs_path / "mesh_parameters").exists()


def test_initialize_configs_creates_default_files(isolated_workspace):
    """Test that initialize_configs creates default configuration files."""
    configs_path = initialize_configs(isolated_workspace)

    # Check that default files exist
    assert (configs_path / "build_parameters" / "default.json").exists()
    assert (configs_path / "materials" / "default.json").exists()
    assert (configs_path / "mesh_parameters" / "default.json").exists()


def test_initialize_configs_idempotent(isolated_workspace):
    """Test that creating configs folder multiple times is idempotent."""
    # Create once
    configs_path_1 = initialize_configs(isolated_workspace)
    assert configs_path_1.exists()

    # Create again (should not error)
    configs_path_2 = initialize_configs(isolated_workspace)
    assert configs_path_2.exists()
    assert configs_path_2 == configs_path_1


# -------------------------------
# Configuration content tests
# -------------------------------


def test_initialize_configs_build_parameters_content(isolated_workspace):
    """Test that build_parameters default file has valid content."""
    configs_path = initialize_configs(isolated_workspace)

    build_params_file = configs_path / "build_parameters" / "default.json"

    # Load the file using BuildParameters
    build_params = BuildParameters.load(build_params_file)

    # Verify it's a valid BuildParameters object
    assert isinstance(build_params, BuildParameters)
    assert build_params.beam_power is not None
    assert build_params.scan_velocity is not None
    assert build_params.beam_diameter is not None


def test_initialize_configs_material_content(isolated_workspace):
    """Test that materials default file has valid content."""
    configs_path = initialize_configs(isolated_workspace)

    material_file = configs_path / "materials" / "default.json"

    # Load the file using Material
    material = Material.load(material_file)

    # Verify it's a valid Material object
    assert isinstance(material, Material)
    assert material.density is not None
    assert material.thermal_conductivity is not None
    assert material.specific_heat_capacity is not None


def test_initialize_configs_mesh_parameters_content(isolated_workspace):
    """Test that mesh_parameters default file has valid content."""
    configs_path = initialize_configs(isolated_workspace)

    mesh_params_file = configs_path / "mesh_parameters" / "default.json"

    # Load the file using MeshParameters
    mesh_params = MeshParameters.load(mesh_params_file)

    # Verify it's a valid MeshParameters object
    assert isinstance(mesh_params, MeshParameters)
    assert mesh_params.x_step is not None
    assert mesh_params.y_step is not None
    assert mesh_params.z_step is not None


# -------------------------------
# Return value tests
# -------------------------------


def test_initialize_configs_return_value(isolated_workspace):
    """Test the structure of return value."""
    configs_path = initialize_configs(isolated_workspace)

    assert isinstance(configs_path, Path)
    assert configs_path.name == "configs"


# -------------------------------
# Edge case tests
# -------------------------------


def test_initialize_configs_with_existing_configs_dir(isolated_workspace):
    """Test creating configs folder when directory already exists."""
    # Pre-create the configs directory
    configs_path = isolated_workspace / "configs"
    configs_path.mkdir()

    # Should not raise an error
    result_path = initialize_configs(isolated_workspace)

    assert result_path.exists()
    assert result_path == configs_path


def test_initialize_configs_overwrites_existing_files(isolated_workspace):
    """Test that initialize_configs overwrites existing config files."""
    configs_path = isolated_workspace / "configs"
    build_params_dir = configs_path / "build_parameters"
    build_params_dir.mkdir(parents=True)

    # Create a dummy file
    test_file = build_params_dir / "default.json"
    test_file.write_text('{"dummy": "content"}')
    original_content = test_file.read_text()

    # Initialize configs should overwrite
    result_path = initialize_configs(isolated_workspace)

    assert test_file.exists()
    # Verify file was overwritten
    new_content = test_file.read_text()
    assert new_content != original_content
    assert "dummy" not in new_content


def test_initialize_configs_with_existing_custom_files(isolated_workspace):
    """Test that custom config files are not deleted."""
    configs_path = isolated_workspace / "configs"
    build_params_dir = configs_path / "build_parameters"
    build_params_dir.mkdir(parents=True)

    # Create a custom config file
    custom_file = build_params_dir / "custom_config.json"
    custom_file.write_text('{"custom": "configuration"}')

    # Initialize configs
    result_path = initialize_configs(isolated_workspace)

    # Custom file should still exist
    assert custom_file.exists()
    assert custom_file.read_text() == '{"custom": "configuration"}'


def test_initialize_configs_invalid_workspace_path(tmp_path):
    """Test that initialize_configs creates parent directories if needed."""
    invalid_path = tmp_path / "nonexistent" / "path" / "to" / "workspace"

    # Should create parent directories and succeed
    configs_path = initialize_configs(invalid_path)
    assert configs_path.exists()
    assert configs_path == invalid_path / "configs"


# -------------------------------
# File integrity tests
# -------------------------------


def test_initialize_configs_all_files_are_valid_json(isolated_workspace):
    """Test that all created config files are valid JSON."""
    import json

    configs_path = initialize_configs(isolated_workspace)

    config_files = [
        configs_path / "build_parameters" / "default.json",
        configs_path / "materials" / "default.json",
        configs_path / "mesh_parameters" / "default.json",
    ]

    for config_file in config_files:
        assert config_file.exists()
        # Should not raise JSONDecodeError
        with open(config_file, "r") as f:
            data = json.load(f)
            assert isinstance(data, dict)


def test_initialize_configs_files_are_loadable(isolated_workspace):
    """Test that all created config files can be loaded by their respective classes."""
    configs_path = initialize_configs(isolated_workspace)

    # Test BuildParameters
    build_params = BuildParameters.load(
        configs_path / "build_parameters" / "default.json"
    )
    assert isinstance(build_params, BuildParameters)

    # Test Material
    material = Material.load(configs_path / "materials" / "default.json")
    assert isinstance(material, Material)

    # Test MeshParameters
    mesh_params = MeshParameters.load(configs_path / "mesh_parameters" / "default.json")
    assert isinstance(mesh_params, MeshParameters)
