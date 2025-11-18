import pytest
import json
from pathlib import Path
from mcp.server.fastmcp import FastMCP

from am.config.mcp import register_config
from am.config import BuildParameters, Material, MeshParameters


# Configure anyio to only use asyncio backend
@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mcp_app():
    """Create a FastMCP app with the config tool registered."""
    app = FastMCP(name="test-config")
    register_config(app)
    return app


@pytest.fixture
def test_workspace(tmp_path):
    """Create a test workspace with config directories."""
    workspace_path = tmp_path / "test_workspace"
    workspace_path.mkdir()

    # Create config directories
    (workspace_path / "configs" / "build_parameters").mkdir(parents=True)
    (workspace_path / "configs" / "materials").mkdir(parents=True)
    (workspace_path / "configs" / "mesh_parameters").mkdir(parents=True)

    return workspace_path


@pytest.fixture
def mock_workspace_lookup(monkeypatch, test_workspace):
    """Mock the workspace lookup to return our test workspace."""

    def mock_get_workspace_path(workspace_name):
        return test_workspace

    # Mock it in wa.cli.utils where it's imported from
    monkeypatch.setattr("wa.cli.utils.get_workspace_path", mock_get_workspace_path)


# -------------------------------
# Schema generation tests
# -------------------------------


def test_config_tool_registered(mcp_app):
    """Test that the config tool is properly registered."""
    tools = mcp_app._tool_manager.list_tools()
    assert len(tools) == 1

    tool = tools[0]
    assert tool.name == "config"
    assert "configuration" in tool.description.lower()


def test_config_tool_has_nested_models(mcp_app):
    """Test that the config tool exposes nested Pydantic models."""
    tools = mcp_app._tool_manager.list_tools()
    tool = tools[0]
    tool_dict = tool.model_dump()
    parameters = tool_dict.get("parameters", {})

    # Check that nested models are defined
    assert "$defs" in parameters
    assert "BuildParametersInput" in parameters["$defs"]
    assert "MaterialInput" in parameters["$defs"]
    assert "MeshParametersInput" in parameters["$defs"]

    # Check top-level parameters reference nested models
    properties = parameters.get("properties", {})
    assert "build_parameters" in properties
    assert "material" in properties
    assert "mesh_parameters" in properties


def test_build_parameters_input_has_all_fields(mcp_app):
    """Test that BuildParametersInput has all expected fields."""
    tools = mcp_app._tool_manager.list_tools()
    tool = tools[0]
    tool_dict = tool.model_dump()
    parameters = tool_dict.get("parameters", {})

    build_params_schema = parameters["$defs"]["BuildParametersInput"]
    properties = build_params_schema["properties"]

    expected_fields = [
        "beam_diameter",
        "beam_power",
        "hatch_spacing",
        "layer_height",
        "scan_velocity",
        "temperature_preheat",
    ]

    for field in expected_fields:
        assert field in properties, f"Missing field: {field}"
        assert properties[field].get("default") is not None


def test_material_input_has_all_fields(mcp_app):
    """Test that MaterialInput has all expected fields."""
    tools = mcp_app._tool_manager.list_tools()
    tool = tools[0]
    tool_dict = tool.model_dump()
    parameters = tool_dict.get("parameters", {})

    material_schema = parameters["$defs"]["MaterialInput"]
    properties = material_schema["properties"]

    expected_fields = [
        "specific_heat_capacity",
        "absorptivity",
        "thermal_conductivity",
        "density",
        "temperature_melt",
        "temperature_liquidus",
        "temperature_solidus",
    ]

    for field in expected_fields:
        assert field in properties, f"Missing field: {field}"


def test_mesh_parameters_input_has_all_fields(mcp_app):
    """Test that MeshParametersInput has all expected fields."""
    tools = mcp_app._tool_manager.list_tools()
    tool = tools[0]
    tool_dict = tool.model_dump()
    parameters = tool_dict.get("parameters", {})

    mesh_schema = parameters["$defs"]["MeshParametersInput"]
    properties = mesh_schema["properties"]

    # Check for key fields (not all 19 to keep test concise)
    key_fields = [
        "x_step",
        "y_step",
        "z_step",
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "z_min",
        "z_max",
        "boundary_condition",
    ]

    for field in key_fields:
        assert field in properties, f"Missing field: {field}"


# -------------------------------
# Functional tests
# -------------------------------


@pytest.mark.anyio
async def test_create_build_parameters_only(
    mcp_app, test_workspace, mock_workspace_lookup
):
    """Test creating only build parameters config."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace",
        name="test_build",
        build_parameters={"beam_power": (300, "watts"), "scan_velocity": (1.0, "m/s")},
    )

    assert result.success is True
    assert "created_files" in result.data
    assert len(result.data["created_files"]) == 1

    # Verify file was created
    expected_path = test_workspace / "configs" / "build_parameters" / "test_build.json"
    assert expected_path.exists()

    # Verify content
    loaded = BuildParameters.load(expected_path)
    assert loaded.beam_power.magnitude == 300
    assert str(loaded.beam_power.units) == "watt"


@pytest.mark.anyio
async def test_create_material_only(mcp_app, test_workspace, mock_workspace_lookup):
    """Test creating only material config."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace",
        name="aluminum",
        material={
            "density": (2700, "kg/m^3"),
            "thermal_conductivity": (237, "W/(m*K)"),
        },
    )

    assert result.success is True
    assert len(result.data["created_files"]) == 1

    # Verify file was created
    expected_path = test_workspace / "configs" / "materials" / "aluminum.json"
    assert expected_path.exists()

    # Verify content
    loaded = Material.load(expected_path)
    assert loaded.density.magnitude == 2700
    assert loaded.thermal_conductivity.magnitude == 237


@pytest.mark.anyio
async def test_create_mesh_parameters_only(
    mcp_app, test_workspace, mock_workspace_lookup
):
    """Test creating only mesh parameters config."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace",
        name="fine_mesh",
        mesh_parameters={
            "x_step": (10, "micrometers"),
            "y_step": (10, "micrometers"),
            "z_step": (10, "micrometers"),
        },
    )

    assert result.success is True
    assert len(result.data["created_files"]) == 1

    # Verify file was created
    expected_path = test_workspace / "configs" / "mesh_parameters" / "fine_mesh.json"
    assert expected_path.exists()

    # Verify content
    loaded = MeshParameters.load(expected_path)
    assert loaded.x_step.magnitude == 10
    assert str(loaded.x_step.units) == "micrometer"


@pytest.mark.anyio
async def test_create_multiple_configs(mcp_app, test_workspace, mock_workspace_lookup):
    """Test creating multiple config files in one call."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace",
        name="multi_config",
        build_parameters={"beam_power": (250, "watts")},
        material={"density": (8000, "kg/m^3")},
        mesh_parameters={"x_step": (20, "micrometers")},
    )

    assert result.success is True
    assert len(result.data["created_files"]) == 3

    # Verify all files were created
    assert (
        test_workspace / "configs" / "build_parameters" / "multi_config.json"
    ).exists()
    assert (test_workspace / "configs" / "materials" / "multi_config.json").exists()
    assert (
        test_workspace / "configs" / "mesh_parameters" / "multi_config.json"
    ).exists()


@pytest.mark.anyio
async def test_create_with_defaults(mcp_app, test_workspace, mock_workspace_lookup):
    """Test creating config with all default values."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace", name="defaults", build_parameters={}
    )

    assert result.success is True

    # Verify file has default values
    expected_path = test_workspace / "configs" / "build_parameters" / "defaults.json"
    loaded = BuildParameters.load(expected_path)

    # Should match DEFAULT values from BuildParameters
    assert loaded.beam_diameter.magnitude == 5e-5
    assert loaded.beam_power.magnitude == 200


@pytest.mark.anyio
async def test_no_config_provided_returns_error(
    mcp_app, test_workspace, mock_workspace_lookup
):
    """Test that providing no configs returns an error."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(workspace="test_workspace", name="empty")

    assert result.success is False
    assert "NO_CONFIG_PROVIDED" in result.error_code


@pytest.mark.anyio
async def test_partial_field_override(mcp_app, test_workspace, mock_workspace_lookup):
    """Test that providing only some fields uses defaults for others."""
    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="test_workspace",
        name="partial",
        build_parameters={"layer_height": (50, "microns")},
    )

    assert result.success is True

    # Load and verify
    expected_path = test_workspace / "configs" / "build_parameters" / "partial.json"
    loaded = BuildParameters.load(expected_path)

    # Custom value
    assert loaded.layer_height.magnitude == 50
    assert str(loaded.layer_height.units) == "micron"

    # Default values
    assert loaded.beam_diameter.magnitude == 5e-5
    assert loaded.beam_power.magnitude == 200


@pytest.mark.anyio
async def test_creates_directories_if_not_exist(tmp_path, mcp_app, monkeypatch):
    """Test that the tool creates config directories if they don't exist."""
    workspace_path = tmp_path / "new_workspace"
    workspace_path.mkdir()

    def mock_get_workspace_path(workspace_name):
        return workspace_path

    import wa.cli.utils

    monkeypatch.setattr(wa.cli.utils, "get_workspace_path", mock_get_workspace_path)

    tools = mcp_app._tool_manager.list_tools()
    config_tool = tools[0]

    result = await config_tool.fn(
        workspace="new_workspace",
        name="test",
        build_parameters={"beam_power": (200, "watts")},
    )

    assert result.success is True
    assert (workspace_path / "configs" / "build_parameters" / "test.json").exists()
