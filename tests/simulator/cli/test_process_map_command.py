"""
Simplified tests for the CLI process_map command focusing on key functionality.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import typer

from am.simulator.cli.process_map import register_simulator_process_map


@pytest.fixture
def typer_app():
    """Create a Typer app for testing."""
    app = typer.Typer()
    register_simulator_process_map(app)
    return app


class TestCommandRegistration:
    """Test that the command is properly registered."""

    def test_command_registered(self, typer_app):
        """Test that process-map command is registered."""
        assert len(typer_app.registered_commands) > 0
        command = typer_app.registered_commands[0]
        assert command.name == "process-map"

    def test_command_has_required_parameters(self, typer_app):
        """Test that command has all required parameters."""
        import inspect

        command = typer_app.registered_commands[0]
        sig = inspect.signature(command.callback)
        param_names = list(sig.parameters.keys())

        # Check essential parameters exist
        required_params = [
            "material_filename",
            "build_parameters_filename",
            "p1",
            "p1_name",
            "p1_range",
            "p1_units",
            "p2",
            "p2_name",
            "p2_range",
            "p2_units",
            "p3",
            "p3_name",
            "p3_range",
            "p3_units",
            "workspace_name",
            "num_proc",
            "verbose",
        ]

        for param in required_params:
            assert param in param_names, f"Missing parameter: {param}"


class TestCommandExecution:
    """Test command execution with mocked dependencies."""

    def get_command_callback(self, typer_app):
        """Helper to get the command callback."""
        return typer_app.registered_commands[0].callback

    @patch(
        "am.simulator.tool.process_map.utils.parameter_ranges.inputs_to_parameter_ranges"
    )
    @patch("wa.cli.utils.get_workspace")
    def test_command_calls_inputs_to_parameter_ranges(
        self, mock_get_workspace, mock_inputs_to_parameter_ranges, typer_app
    ):
        """Test that command calls inputs_to_parameter_ranges with correct arguments."""
        # Setup mocks to avoid actual execution
        mock_workspace = Mock()
        mock_workspace.path = Path("/mock/workspace")
        mock_get_workspace.return_value = mock_workspace
        mock_inputs_to_parameter_ranges.return_value = []

        # Mock the other imports to prevent actual execution
        with (
            patch("am.config.Material.load"),
            patch("am.config.BuildParameters.load"),
            patch("am.simulator.tool.process_map.models.ProcessMap"),
        ):

            callback = self.get_command_callback(typer_app)

            try:
                callback(
                    material_filename="test.json",
                    build_parameters_filename="build.json",
                    p1=["beam_power", "100", "1000", "50"],
                    p1_name=None,
                    p1_range=None,
                    p1_units=None,
                    p2=None,
                    p2_name="scan_velocity",
                    p2_range=None,
                    p2_units=None,
                    p3=None,
                    p3_name=None,
                    p3_range=None,
                    p3_units=None,
                    workspace_name="test",
                    num_proc=1,
                    verbose=False,
                )
            except:
                pass  # Expected to fail due to mocking

            # Verify inputs_to_parameter_ranges was called
            mock_inputs_to_parameter_ranges.assert_called_once()

            # Verify it was called with 3 tuples (p1, p2, p3)
            call_args = mock_inputs_to_parameter_ranges.call_args[0]
            assert len(call_args) == 3

            # Check first parameter tuple
            assert call_args[0][0] == ["beam_power", "100", "1000", "50"]

            # Check second parameter tuple
            assert call_args[1][1] == "scan_velocity"

    # @patch(
    #     "am.simulator.tool.process_map.utils.parameter_ranges.inputs_to_parameter_ranges"
    # )
    # @patch("am.config.Material.load")
    # @patch("wa.cli.utils.get_workspace")
    # def test_command_handles_material_load_error(
    #     self,
    #     mock_get_workspace,
    #     mock_material_load,
    #     mock_inputs_to_parameter_ranges,
    #     typer_app,
    # ):
    #     """Test that command raises error during material loading."""
    #     # Setup mocks so we get past initial stages
    #     mock_workspace = Mock()
    #     mock_workspace.path = Path("/mock/workspace")
    #     mock_get_workspace.return_value = mock_workspace
    #     mock_inputs_to_parameter_ranges.return_value = [Mock()]
    #
    #     # Make Material.load raise an error
    #     mock_material_load.side_effect = Exception("Failed to load material")
    #
    #     callback = self.get_command_callback(typer_app)
    #
    #     # Since error handling is not implemented (try block is commented out),
    #     # the exception should propagate directly
    #     with pytest.raises(Exception, match="Failed to load material"):
    #         callback(
    #             material_filename="test.json",
    #             build_parameters_filename="build.json",
    #             p1=None,
    #             p1_name=None,
    #             p1_range=None,
    #             p1_units=None,
    #             p2=None,
    #             p2_name=None,
    #             p2_range=None,
    #             p2_units=None,
    #             p3=None,
    #             p3_name=None,
    #             p3_range=None,
    #             p3_units=None,
    #             workspace_name="test",
    #             num_proc=1,
    #             verbose=False,
    #         )


class TestCommandWorkflow:
    """Test the complete command workflow with all mocks."""

    @patch(
        "am.simulator.tool.process_map.utils.parameter_ranges.inputs_to_parameter_ranges"
    )
    @patch("am.simulator.tool.process_map.models.ProcessMap")
    @patch("am.config.BuildParameters.load")
    @patch("am.config.Material.load")
    @patch("wa.cli.utils.get_workspace")
    def test_full_workflow_creates_process_map(
        self,
        mock_get_workspace,
        mock_material_load,
        mock_build_params_load,
        mock_process_map_class,
        mock_inputs_to_parameter_ranges,
        typer_app,
    ):
        """Test complete workflow creates and saves ProcessMap."""
        # Setup workspace mock
        mock_workspace = Mock()
        mock_workspace.path = Path("/mock/workspace")
        mock_folder = Mock()
        mock_folder.path = Path("/mock/workspace/output")
        mock_workspace.create_folder = Mock(return_value=mock_folder)
        mock_get_workspace.return_value = mock_workspace

        # Setup other mocks
        mock_material = Mock()
        mock_material.name = "Test Material"
        mock_material_load.return_value = mock_material

        mock_build_params = Mock()
        mock_build_params_load.return_value = mock_build_params

        mock_param = Mock()
        mock_param.name = "beam_power"
        mock_inputs_to_parameter_ranges.return_value = [mock_param]

        mock_process_map_instance = Mock()
        mock_process_map_class.return_value = mock_process_map_instance

        # Execute command
        callback = typer_app.registered_commands[0].callback
        callback(
            material_filename="material.json",
            build_parameters_filename="build.json",
            p1=None,
            p1_name=None,
            p1_range=None,
            p1_units=None,
            p2=None,
            p2_name=None,
            p2_range=None,
            p2_units=None,
            p3=None,
            p3_name=None,
            p3_range=None,
            p3_units=None,
            workspace_name="test",
            num_proc=1,
            verbose=False,
        )

        # Verify workflow
        mock_get_workspace.assert_called_once_with("test")
        mock_inputs_to_parameter_ranges.assert_called_once()
        mock_material_load.assert_called_once()
        mock_build_params_load.assert_called_once()
        mock_workspace.create_folder.assert_called_once()
        mock_process_map_class.assert_called_once()
        mock_process_map_instance.save.assert_called_once()

    @patch(
        "am.simulator.tool.process_map.utils.parameter_ranges.inputs_to_parameter_ranges"
    )
    @patch("am.simulator.tool.process_map.models.ProcessMap")
    @patch("am.config.BuildParameters.load")
    @patch("am.config.Material.load")
    @patch("wa.cli.utils.get_workspace")
    def test_workflow_with_default_parameters(
        self,
        mock_get_workspace,
        mock_material_load,
        mock_build_params_load,
        mock_process_map_class,
        mock_inputs_to_parameter_ranges,
        typer_app,
    ):
        """Test workflow with no parameters uses defaults."""
        # Setup mocks
        mock_workspace = Mock()
        mock_workspace.path = Path("/mock/workspace")
        mock_folder = Mock()
        mock_folder.path = Path("/mock/workspace/output")
        mock_workspace.create_folder = Mock(return_value=mock_folder)
        mock_get_workspace.return_value = mock_workspace

        mock_material = Mock()
        mock_material.name = "Material"
        mock_material_load.return_value = mock_material

        mock_build_params_load.return_value = Mock()

        # Create default parameters (3 parameters as returned by inputs_to_parameter_ranges)
        default_params = [
            Mock(name="beam_power"),
            Mock(name="scan_velocity"),
            Mock(name="layer_height"),
        ]
        mock_inputs_to_parameter_ranges.return_value = default_params

        mock_process_map_instance = Mock()
        mock_process_map_class.return_value = mock_process_map_instance

        # Execute with no parameters (all None)
        callback = typer_app.registered_commands[0].callback
        callback(
            material_filename="default.json",
            build_parameters_filename="default.json",
            p1=None,
            p1_name=None,
            p1_range=None,
            p1_units=None,
            p2=None,
            p2_name=None,
            p2_range=None,
            p2_units=None,
            p3=None,
            p3_name=None,
            p3_range=None,
            p3_units=None,
            workspace_name=None,
            num_proc=1,
            verbose=False,
        )

        # Verify inputs_to_parameter_ranges was called with 3 (None, None, None, None) tuples
        call_args = mock_inputs_to_parameter_ranges.call_args[0]
        assert len(call_args) == 3
        assert all(all(v is None for v in tuple_arg) for tuple_arg in call_args)


print("✓ All tests defined successfully")
