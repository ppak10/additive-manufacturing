import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.config import BuildParameters

# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_create_default_returns_quantities():
    params = BuildParameters()
    assert isinstance(params.beam_diameter, Quantity)
    assert params.beam_diameter.magnitude == 5e-5
    assert str(params.beam_diameter.units) == "meter"
    assert params.beam_power.magnitude == 200
    assert str(params.beam_power.units) == "watt"  # pint normalizes plural
    assert params.scan_velocity.magnitude == 0.8
    assert str(params.scan_velocity.units) == "meter / second"
    assert params.temperature_preheat.magnitude == 300
    assert str(params.temperature_preheat.units) == "kelvin"


def test_valid_build_parameters_parsing_from_quantity():
    data = {
        "beam_diameter": Quantity(1e-4, "meter"),
        "beam_power": Quantity(250, "watt"),
        "scan_velocity": Quantity(1.0, "meter / second"),
        "temperature_preheat": Quantity(350, "kelvin"),
    }
    params = BuildParameters(**data)
    for key, value in data.items():
        q = getattr(params, key)
        assert isinstance(q, Quantity)
        assert q.magnitude == value.magnitude
        assert str(q.units) == str(value.units)


def test_valid_build_parameters_parsing_from_float_defaults():
    """Passing only numbers should use default units from _quantity_defaults."""
    data = {
        "beam_diameter": 1e-4,
        "beam_power": 250,
        "scan_velocity": 1.0,
        "temperature_preheat": 350,
    }
    params = BuildParameters(**data)
    assert str(params.beam_diameter.units) == "meter"
    assert str(params.beam_power.units) == "watt"
    assert str(params.scan_velocity.units) == "meter / second"
    assert str(params.temperature_preheat.units) == "kelvin"


def test_valid_build_parameters_parsing_from_tuple():
    """(magnitude, unit) tuples should override default units."""
    data = {
        "beam_diameter": (1e-4, "millimeter"),
        "beam_power": (300, "kilowatt"),
        "scan_velocity": (2, "centimeter / second"),
        "temperature_preheat": (573, "kelvin"),
    }
    params = BuildParameters(**data)
    assert str(params.beam_diameter.units) == "millimeter"
    assert str(params.beam_power.units) == "kilowatt"
    assert str(params.scan_velocity.units) == "centimeter / second"
    assert str(params.temperature_preheat.units) == "kelvin"


def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        BuildParameters(
            beam_diameter="not_a_quantity",
            beam_power=Quantity(200, "watt"),
            scan_velocity=Quantity(1.0, "meter / second"),
            temperature_preheat=Quantity(300, "kelvin"),
        )


# -------------------------------
# Serialization tests
# -------------------------------


def test_build_parameters_to_dict():
    build_parameters = BuildParameters()
    serialized = build_parameters.to_dict(
        verbose=True
    )  # Use verbose format for dict output
    for field in [
        "beam_diameter",
        "beam_power",
        "scan_velocity",
        "temperature_preheat",
    ]:
        q_dict = serialized[field]
        q = getattr(build_parameters, field)
        assert q_dict["magnitude"] == q.magnitude
        assert q_dict["units"] == str(q.units)


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load(tmp_path: Path):
    params = BuildParameters()
    path = tmp_path / "params.json"
    saved_path = params.save(path)
    assert saved_path.exists()

    loaded_params = BuildParameters.load(saved_path)
    for field in [
        "beam_diameter",
        "beam_power",
        "scan_velocity",
        "temperature_preheat",
    ]:
        original = getattr(params, field)
        loaded = getattr(loaded_params, field)
        assert loaded.magnitude == original.magnitude
        assert str(loaded.units) == str(original.units)
