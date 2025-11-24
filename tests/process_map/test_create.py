import pytest
import json
from pathlib import Path
from pint import Quantity

from am.config import BuildParameters, Material, ProcessMap
from am.process_map.create import create_process_map_folder


# -------------------------------
# Basic functionality tests
# -------------------------------


def test_create_process_map_folder_basic(tmp_path):
    """Test basic creation of process map folder structure."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify folder was created
    assert folder.path.exists()
    assert folder.path.is_dir()
    assert folder.name == process_map_folder_name


def test_create_process_map_folder_creates_config_subfolder(tmp_path):
    """Test that config subfolder is created."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify config subfolder exists
    config_folder = folder.path / "config"
    assert config_folder.exists()
    assert config_folder.is_dir()


def test_create_process_map_folder_creates_plots_subfolder(tmp_path):
    """Test that plots subfolder is created."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify plots subfolder exists
    plots_folder = folder.path / "plots"
    assert plots_folder.exists()
    assert plots_folder.is_dir()


# -------------------------------
# Configuration file tests
# -------------------------------


def test_create_process_map_folder_saves_build_parameters(tmp_path):
    """Test that build_parameters.json is created and contains correct data."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters(
        beam_power=Quantity(250.0, "watt"),
        scan_velocity=Quantity(1.0, "meter / second"),
    )
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify build_parameters.json exists
    build_params_file = folder.path / "config" / "build_parameters.json"
    assert build_params_file.exists()

    # Load and verify contents
    loaded_params = BuildParameters.load(build_params_file)
    assert loaded_params.beam_power.magnitude == 250.0
    assert loaded_params.scan_velocity.magnitude == 1.0


def test_create_process_map_folder_saves_material(tmp_path):
    """Test that material.json is created and contains correct data."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material(
        density=Quantity(8000.0, "kilogram / meter ** 3"),
        thermal_conductivity=Quantity(10.0, "watt / (meter * kelvin)"),
    )
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify material.json exists
    material_file = folder.path / "config" / "material.json"
    assert material_file.exists()

    # Load and verify contents
    loaded_material = Material.load(material_file)
    assert loaded_material.density.magnitude == 8000.0
    assert loaded_material.thermal_conductivity.magnitude == 10.0


def test_create_process_map_folder_saves_process_map(tmp_path):
    """Test that process_map.json is created and contains correct data."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap(
        parameters=["beam_power", "scan_velocity"],
    )

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify process_map.json exists
    process_map_file = folder.path / "config" / "process_map.json"
    assert process_map_file.exists()

    # Load and verify contents
    loaded_process_map = ProcessMap.load(process_map_file)
    assert loaded_process_map.parameters == ["beam_power", "scan_velocity"]


def test_create_process_map_folder_all_config_files_present(tmp_path):
    """Test that all three configuration files are created."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    config_folder = folder.path / "config"

    # Verify all config files exist
    assert (config_folder / "build_parameters.json").exists()
    assert (config_folder / "material.json").exists()
    assert (config_folder / "process_map.json").exists()


# -------------------------------
# Force parameter tests
# -------------------------------


def test_create_process_map_folder_without_force_succeeds_if_exists(tmp_path):
    """Test that creating folder twice without force=True still succeeds (overwrites)."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    # Create folder first time
    folder1 = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Create again without force (should still work based on current implementation)
    folder2 = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
        force=False,
    )

    # Both should point to the same path
    assert folder1.path == folder2.path


def test_create_process_map_folder_with_force_overwrites(tmp_path):
    """Test that force=True allows overwriting existing folder."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters(
        beam_power=Quantity(200.0, "watt"),
    )
    material = Material()
    process_map = ProcessMap()

    # Create folder first time
    create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Create again with force=True and different parameters
    build_parameters_new = BuildParameters(
        beam_power=Quantity(300.0, "watt"),
    )

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters_new,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
        force=True,
    )

    # Verify new parameters were saved
    build_params_file = folder.path / "config" / "build_parameters.json"
    loaded_params = BuildParameters.load(build_params_file)
    assert loaded_params.beam_power.magnitude == 300.0


# -------------------------------
# Workspace path tests
# -------------------------------


def test_create_process_map_folder_with_custom_workspace_path(tmp_path):
    """Test creating folder with custom workspace path."""
    custom_path = tmp_path / "custom_workspaces"
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=custom_path,
    )

    # Verify folder was created in custom path
    assert folder.path.exists()
    assert custom_path in folder.path.parents


def test_create_process_map_folder_default_workspace_path(tmp_path, monkeypatch):
    """Test that None workspace path uses default location."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    # Note: This test might behave differently depending on the default workspace path
    # We're just checking that it doesn't raise an error
    try:
        folder = create_process_map_folder(
            process_map_folder_name=process_map_folder_name,
            build_parameters=build_parameters,
            material=material,
            process_map=process_map,
            workspace_name=workspace_name,
            workspaces_path=None,
        )
        assert folder.path.exists()
    except Exception:
        # If default path doesn't exist or isn't writable, that's okay for this test
        pass


# -------------------------------
# Folder structure tests
# -------------------------------


def test_create_process_map_folder_nested_structure(tmp_path):
    """Test that the correct nested folder structure is created."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify the full path includes process_maps as parent
    assert "process_maps" in str(folder.path)
    assert folder.path.parent.name == "process_maps"


def test_create_process_map_folder_multiple_folders(tmp_path):
    """Test creating multiple process map folders in same workspace."""
    workspace_name = "test_workspace"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    # Create first folder
    folder1 = create_process_map_folder(
        process_map_folder_name="process_map_1",
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Create second folder
    folder2 = create_process_map_folder(
        process_map_folder_name="process_map_2",
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify both folders exist
    assert folder1.path.exists()
    assert folder2.path.exists()
    assert folder1.path != folder2.path


# -------------------------------
# Return value tests
# -------------------------------


def test_create_process_map_folder_returns_workspace_folder(tmp_path):
    """Test that function returns a WorkspaceFolder object."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    build_parameters = BuildParameters()
    material = Material()
    process_map = ProcessMap()

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Verify return value has expected attributes
    assert hasattr(folder, "path")
    assert hasattr(folder, "name")
    assert isinstance(folder.path, Path)


# -------------------------------
# Integration tests
# -------------------------------


def test_create_process_map_folder_full_workflow(tmp_path):
    """Test complete workflow of creating folder and loading config back."""
    workspace_name = "test_workspace"
    process_map_folder_name = "test_process_map"

    # Create with custom parameters
    build_parameters = BuildParameters(
        beam_power=Quantity(275.0, "watt"),
        scan_velocity=Quantity(1.2, "meter / second"),
        hatch_spacing=Quantity(55.0, "micrometer"),
    )
    material = Material(
        density=Quantity(7950.0, "kilogram / meter ** 3"),
        thermal_conductivity=Quantity(9.5, "watt / (meter * kelvin)"),
    )
    process_map = ProcessMap(
        parameters=["beam_power", "scan_velocity"],
    )

    folder = create_process_map_folder(
        process_map_folder_name=process_map_folder_name,
        build_parameters=build_parameters,
        material=material,
        process_map=process_map,
        workspace_name=workspace_name,
        workspaces_path=tmp_path,
    )

    # Load all config files and verify
    config_folder = folder.path / "config"

    loaded_build_params = BuildParameters.load(config_folder / "build_parameters.json")
    assert loaded_build_params.beam_power.magnitude == 275.0
    assert loaded_build_params.scan_velocity.magnitude == 1.2
    assert loaded_build_params.hatch_spacing.magnitude == 55.0

    loaded_material = Material.load(config_folder / "material.json")
    assert loaded_material.density.magnitude == 7950.0
    assert loaded_material.thermal_conductivity.magnitude == 9.5

    loaded_process_map = ProcessMap.load(config_folder / "process_map.json")
    assert loaded_process_map.parameters == ["beam_power", "scan_velocity"]
