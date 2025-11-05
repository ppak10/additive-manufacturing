import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.config.mesh_parameters import MeshParameters

# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_create_default_returns_quantities():
    params = MeshParameters()
    assert isinstance(params.x_step, Quantity)
    assert params.x_step.magnitude == 25
    assert str(params.x_step.units) == "micrometer"
    assert params.y_step.magnitude == 25
    assert str(params.y_step.units) == "micrometer"
    assert params.z_step.magnitude == 25
    assert str(params.z_step.units) == "micrometer"
    assert params.x_min.magnitude == 0.0
    assert str(params.x_min.units) == "millimeter"
    assert params.x_max.magnitude == 10.0
    assert str(params.x_max.units) == "millimeter"
    assert params.boundary_condition == "temperature"


def test_valid_mesh_parameters_parsing_from_quantity():
    data = {
        "x_step": Quantity(50, "micrometer"),
        "y_step": Quantity(50, "micrometer"),
        "z_step": Quantity(50, "micrometer"),
        "x_min": Quantity(0.0, "millimeter"),
        "x_max": Quantity(5.0, "millimeter"),
        "y_min": Quantity(0.0, "millimeter"),
        "y_max": Quantity(5.0, "millimeter"),
        "z_min": Quantity(-1.0, "millimeter"),
        "z_max": Quantity(0.0, "millimeter"),
        "x_initial": Quantity(0.0, "millimeter"),
        "y_initial": Quantity(0.0, "millimeter"),
        "z_initial": Quantity(0.0, "millimeter"),
        "x_start_pad": Quantity(0.1, "millimeter"),
        "y_start_pad": Quantity(0.1, "millimeter"),
        "z_start_pad": Quantity(0.0, "millimeter"),
        "x_end_pad": Quantity(0.1, "millimeter"),
        "y_end_pad": Quantity(0.1, "millimeter"),
        "z_end_pad": Quantity(0.05, "millimeter"),
        "boundary_condition": "flux",
    }
    params = MeshParameters(**data)
    for key, value in data.items():
        attr = getattr(params, key)
        if isinstance(value, Quantity):
            assert isinstance(attr, Quantity)
            assert attr.magnitude == value.magnitude
            assert str(attr.units) == str(value.units)
        else:
            assert attr == value


def test_valid_mesh_parameters_parsing_from_float_defaults():
    """Passing only numbers should use default units from DEFAULT."""
    data = {
        "x_step": 50,
        "y_step": 50,
        "z_step": 50,
        "x_min": 0.0,
        "x_max": 5.0,
        "y_min": 0.0,
        "y_max": 5.0,
        "z_min": -1.0,
        "z_max": 0.0,
        "x_initial": 0.0,
        "y_initial": 0.0,
        "z_initial": 0.0,
        "x_start_pad": 0.1,
        "y_start_pad": 0.1,
        "z_start_pad": 0.0,
        "x_end_pad": 0.1,
        "y_end_pad": 0.1,
        "z_end_pad": 0.05,
    }
    params = MeshParameters(**data)
    assert str(params.x_step.units) == "micrometer"
    assert str(params.y_step.units) == "micrometer"
    assert str(params.z_step.units) == "micrometer"
    assert str(params.x_min.units) == "millimeter"
    assert str(params.x_max.units) == "millimeter"


def test_valid_mesh_parameters_parsing_from_tuple():
    """(magnitude, unit) tuples should override default units."""
    data = {
        "x_step": (100, "nanometer"),
        "y_step": (100, "nanometer"),
        "z_step": (100, "nanometer"),
        "x_min": (0.0, "meter"),
        "x_max": (0.01, "meter"),
        "y_min": (0.0, "meter"),
        "y_max": (0.01, "meter"),
        "z_min": (-0.001, "meter"),
        "z_max": (0.0, "meter"),
        "x_initial": (0.0, "meter"),
        "y_initial": (0.0, "meter"),
        "z_initial": (0.0, "meter"),
        "x_start_pad": (0.0002, "meter"),
        "y_start_pad": (0.0002, "meter"),
        "z_start_pad": (0.0, "meter"),
        "x_end_pad": (0.0002, "meter"),
        "y_end_pad": (0.0002, "meter"),
        "z_end_pad": (0.0001, "meter"),
        "boundary_condition": "flux",
    }
    params = MeshParameters(**data)
    assert str(params.x_step.units) == "nanometer"
    assert str(params.y_step.units) == "nanometer"
    assert str(params.x_min.units) == "meter"
    assert str(params.x_max.units) == "meter"
    assert params.boundary_condition == "flux"


def test_boundary_condition_validation():
    """Test that boundary_condition only accepts valid literals."""
    params = MeshParameters(boundary_condition="flux")
    assert params.boundary_condition == "flux"

    params = MeshParameters(boundary_condition="temperature")
    assert params.boundary_condition == "temperature"


def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        MeshParameters(
            x_step="not_a_quantity",
            y_step=Quantity(50, "micrometer"),
            z_step=Quantity(50, "micrometer"),
        )


# -------------------------------
# Serialization tests
# -------------------------------


def test_mesh_parameters_to_dict():
    mesh_parameters = MeshParameters()
    serialized = mesh_parameters.to_dict()
    quantity_fields = [
        "x_step", "y_step", "z_step",
        "x_min", "x_max", "y_min", "y_max", "z_min", "z_max",
        "x_initial", "y_initial", "z_initial",
        "x_start_pad", "y_start_pad", "z_start_pad",
        "x_end_pad", "y_end_pad", "z_end_pad",
    ]
    for field in quantity_fields:
        q_dict = serialized[field]
        q = getattr(mesh_parameters, field)
        assert q_dict["magnitude"] == q.magnitude
        assert q_dict["units"] == str(q.units)
    assert serialized["boundary_condition"] == "temperature"


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load(tmp_path: Path):
    params = MeshParameters()
    path = tmp_path / "mesh_params.json"
    saved_path = params.save(path)
    assert saved_path.exists()

    loaded_params = MeshParameters.load(saved_path)
    quantity_fields = [
        "x_step", "y_step", "z_step",
        "x_min", "x_max", "y_min", "y_max", "z_min", "z_max",
        "x_initial", "y_initial", "z_initial",
        "x_start_pad", "y_start_pad", "z_start_pad",
        "x_end_pad", "y_end_pad", "z_end_pad",
    ]
    for field in quantity_fields:
        original = getattr(params, field)
        loaded = getattr(loaded_params, field)
        assert loaded.magnitude == original.magnitude
        assert str(loaded.units) == str(original.units)
    assert loaded_params.boundary_condition == params.boundary_condition


# -------------------------------
# Property tests
# -------------------------------


def test_x_start_property():
    """Test that x_start returns properly typed Quantity."""
    params = MeshParameters(
        x_min=Quantity(5.0, "millimeter"),
        x_start_pad=Quantity(1.0, "millimeter"),
    )
    result = params.x_start
    assert isinstance(result, Quantity)
    assert result.magnitude == 4.0
    assert str(result.units) == "millimeter"


def test_x_end_property():
    """Test that x_end returns properly typed Quantity."""
    params = MeshParameters(
        x_max=Quantity(10.0, "millimeter"),
        x_end_pad=Quantity(2.0, "millimeter"),
    )
    result = params.x_end
    assert isinstance(result, Quantity)
    assert result.magnitude == 12.0
    assert str(result.units) == "millimeter"


def test_y_start_property():
    """Test that y_start returns properly typed Quantity."""
    params = MeshParameters(
        y_min=Quantity(3.0, "millimeter"),
        y_start_pad=Quantity(0.5, "millimeter"),
    )
    result = params.y_start
    assert isinstance(result, Quantity)
    assert result.magnitude == 2.5
    assert str(result.units) == "millimeter"


def test_y_end_property():
    """Test that y_end returns properly typed Quantity."""
    params = MeshParameters(
        y_max=Quantity(8.0, "millimeter"),
        y_end_pad=Quantity(1.5, "millimeter"),
    )
    result = params.y_end
    assert isinstance(result, Quantity)
    assert result.magnitude == 9.5
    assert str(result.units) == "millimeter"


def test_z_start_property():
    """Test that z_start returns properly typed Quantity."""
    params = MeshParameters(
        z_min=Quantity(-0.5, "millimeter"),
        z_start_pad=Quantity(0.2, "millimeter"),
    )
    result = params.z_start
    assert isinstance(result, Quantity)
    assert result.magnitude == -0.7
    assert str(result.units) == "millimeter"


def test_z_end_property():
    """Test that z_end returns properly typed Quantity."""
    params = MeshParameters(
        z_max=Quantity(0.0, "millimeter"),
        z_end_pad=Quantity(0.3, "millimeter"),
    )
    result = params.z_end
    assert isinstance(result, Quantity)
    assert result.magnitude == 0.3
    assert str(result.units) == "millimeter"
