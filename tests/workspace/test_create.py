import pytest
from pathlib import Path
from unittest.mock import patch

from am.workspace.create import (
    create_additive_manufacturing_workspace,
    create_workspace_configs_folder,
    create_workspace_parts_folder,
)
from am.config import BuildParameters, Material, MeshParameters
from wa.models import Workspace, WorkspaceFolder


# =============================================================================
# Tests for create_additive_manufacturing_workspace
# =============================================================================


class TestCreateAdditiveManufacturingWorkspace:
    """Tests for the main workspace creation function."""

    def test_basic_creation(self, isolated_workspace):
        """Test creating a basic workspace."""
        workspace = create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        assert isinstance(workspace, Workspace)
        assert workspace.name == "test"

    def test_creates_workspace_directory(self, isolated_workspace):
        """Test that workspace directory is created."""
        workspace = create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        workspace_dir = isolated_workspace / "test"
        assert workspace_dir.exists()
        assert workspace_dir.is_dir()

    def test_creates_configs_folder(self, isolated_workspace):
        """Test that configs folder is created with subdirectories."""
        create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        configs_path = isolated_workspace / "test" / "configs"
        assert configs_path.exists()
        assert (configs_path / "build_parameters").exists()
        assert (configs_path / "material").exists()
        assert (configs_path / "mesh_parameters").exists()

    def test_creates_parts_folder(self, isolated_workspace):
        """Test that parts folder is created."""
        create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        parts_path = isolated_workspace / "test" / "parts"
        assert parts_path.exists()
        assert parts_path.is_dir()

    def test_creates_default_config_files(self, isolated_workspace):
        """Test that default config files are created."""
        create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        configs_path = isolated_workspace / "test" / "configs"
        assert (configs_path / "build_parameters" / "default.json").exists()
        assert (configs_path / "material" / "default.json").exists()
        assert (configs_path / "mesh_parameters" / "default.json").exists()

    def test_with_examples(self, isolated_workspace):
        """Test creating workspace with example files."""
        create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=True,
        )

        parts_path = isolated_workspace / "test" / "parts"
        expected_files = ["overhang.STL", "overhang.gcode", "README.md"]
        for file_name in expected_files:
            assert (parts_path / file_name).exists()

    def test_with_force(self, isolated_workspace):
        """Test recreating workspace with force=True."""
        # Create once
        workspace_1 = create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        # Create again with force
        workspace_2 = create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            force=True,
        )

        # Verify workspace still exists
        workspace_dir = isolated_workspace / "test"
        assert workspace_dir.exists()
        assert (workspace_dir / "configs").exists()
        assert (workspace_dir / "parts").exists()

    def test_config_files_are_loadable(self, isolated_workspace):
        """Test that all created config files can be loaded."""
        create_additive_manufacturing_workspace(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        configs_path = isolated_workspace / "test" / "configs"

        build_params = BuildParameters.load(
            configs_path / "build_parameters" / "default.json"
        )
        assert isinstance(build_params, BuildParameters)

        material = Material.load(configs_path / "material" / "default.json")
        assert isinstance(material, Material)

        mesh_params = MeshParameters.load(
            configs_path / "mesh_parameters" / "default.json"
        )
        assert isinstance(mesh_params, MeshParameters)


# =============================================================================
# Tests for create_workspace_configs_folder
# =============================================================================


class TestCreateWorkspaceConfigsFolder:
    """Tests for the configs folder creation function."""

    def test_basic_creation(self, isolated_workspace):
        """Test creating configs folder with default configurations."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        assert configs_folder.path.exists()
        assert configs_folder.path.is_dir()
        assert configs_folder.path == isolated_workspace / "test" / "configs"

    def test_creates_subdirectories(self, isolated_workspace):
        """Test that necessary subdirectories are created."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        assert (configs_folder.path / "build_parameters").exists()
        assert (configs_folder.path / "material").exists()
        assert (configs_folder.path / "mesh_parameters").exists()

    def test_creates_default_files(self, isolated_workspace):
        """Test that default configuration files are created."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        assert (configs_folder.path / "build_parameters" / "default.json").exists()
        assert (configs_folder.path / "material" / "default.json").exists()
        assert (configs_folder.path / "mesh_parameters" / "default.json").exists()

    def test_with_force(self, isolated_workspace):
        """Test that creating configs folder with force=True works."""
        # Create once
        configs_folder_1 = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )
        assert configs_folder_1.path.exists()

        # Create again with force
        create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            force=True,
        )

        expected_path = isolated_workspace / "test" / "configs"
        assert expected_path.exists()
        assert (expected_path / "build_parameters" / "default.json").exists()

    def test_build_parameters_content(self, isolated_workspace):
        """Test that build_parameters default file has valid content."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        build_params_file = configs_folder.path / "build_parameters" / "default.json"
        build_params = BuildParameters.load(build_params_file)

        assert isinstance(build_params, BuildParameters)
        assert build_params.beam_power is not None
        assert build_params.scan_velocity is not None
        assert build_params.beam_diameter is not None

    def test_material_content(self, isolated_workspace):
        """Test that material default file has valid content."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        material_file = configs_folder.path / "material" / "default.json"
        material = Material.load(material_file)

        assert isinstance(material, Material)
        assert material.density is not None
        assert material.thermal_conductivity is not None
        assert material.specific_heat_capacity is not None

    def test_mesh_parameters_content(self, isolated_workspace):
        """Test that mesh_parameters default file has valid content."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        mesh_params_file = configs_folder.path / "mesh_parameters" / "default.json"
        mesh_params = MeshParameters.load(mesh_params_file)

        assert isinstance(mesh_params, MeshParameters)
        assert mesh_params.x_step is not None
        assert mesh_params.y_step is not None
        assert mesh_params.z_step is not None

    def test_return_value(self, isolated_workspace):
        """Test the structure of return value."""
        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        assert isinstance(configs_folder, WorkspaceFolder)
        assert configs_folder.path.name == "configs"

    def test_all_files_are_valid_json(self, isolated_workspace):
        """Test that all created config files are valid JSON."""
        import json

        configs_folder = create_workspace_configs_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
        )

        config_files = [
            configs_folder.path / "build_parameters" / "default.json",
            configs_folder.path / "material" / "default.json",
            configs_folder.path / "mesh_parameters" / "default.json",
        ]

        for config_file in config_files:
            assert config_file.exists()
            with open(config_file, "r") as f:
                data = json.load(f)
                assert isinstance(data, dict)


# =============================================================================
# Tests for create_workspace_parts_folder
# =============================================================================


class TestCreateWorkspacePartsFolder:
    """Tests for the parts folder creation function."""

    def test_basic_creation(self, isolated_workspace):
        """Test creating a basic parts folder without examples."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=False,
        )

        assert parts_folder.path.exists()
        assert parts_folder.path.is_dir()
        assert parts_folder.path == isolated_workspace / "test" / "parts"

    def test_with_force(self, isolated_workspace):
        """Test that creating parts folder with force=True works."""
        # Create once
        parts_folder_1 = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=False,
        )
        assert parts_folder_1.path.exists()

        # Create again with force
        create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            force=True,
            include_examples=False,
        )

        expected_path = isolated_workspace / "test" / "parts"
        assert expected_path.exists()

    def test_with_examples(self, isolated_workspace):
        """Test creating parts folder with example files."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=True,
        )

        assert parts_folder.path.exists()
        assert parts_folder.path.is_dir()

        expected_files = ["overhang.STL", "overhang.gcode", "README.md"]
        for file_name in expected_files:
            assert (parts_folder.path / file_name).exists()

    def test_example_file_contents(self, isolated_workspace):
        """Test that copied files are identical to source files."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=True,
        )

        from am.data import DATA_DIR

        data_parts_dir = DATA_DIR / "parts"

        for file_path in data_parts_dir.iterdir():
            if file_path.is_file():
                dest_file = parts_folder.path / file_path.name

                assert dest_file.exists()
                assert dest_file.stat().st_size == file_path.stat().st_size

                if file_path.name.endswith((".md", ".gcode")):
                    assert dest_file.read_text() == file_path.read_text()

    def test_preserves_custom_files(self, isolated_workspace):
        """Test that custom files are preserved when creating parts folder."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=True,
        )

        custom_file = parts_folder.path / "my_custom_part.stl"
        custom_file.write_text("custom content")

        assert custom_file.exists()
        assert custom_file.read_text() == "custom content"
        assert (parts_folder.path / "overhang.STL").exists()
        assert (parts_folder.path / "README.md").exists()

    def test_return_value_without_examples(self, isolated_workspace):
        """Test the structure of return value when not including examples."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=False,
        )

        assert isinstance(parts_folder, WorkspaceFolder)

    def test_return_value_with_examples(self, isolated_workspace):
        """Test the structure of return value when including examples."""
        parts_folder = create_workspace_parts_folder(
            workspace_name="test",
            workspaces_path=isolated_workspace,
            include_examples=True,
        )

        assert isinstance(parts_folder, WorkspaceFolder)

    def test_empty_data_directory(self, isolated_workspace):
        """Test behavior when data/parts directory exists but is empty."""
        mock_data_dir = isolated_workspace / "mock_data"
        mock_data_parts = mock_data_dir / "parts"
        mock_data_parts.mkdir(parents=True)

        with patch("am.data.DATA_DIR", mock_data_dir):
            parts_folder = create_workspace_parts_folder(
                workspace_name="test",
                workspaces_path=isolated_workspace,
                include_examples=True,
            )

            assert parts_folder.path.exists()
            assert len(list(parts_folder.path.iterdir())) == 0
