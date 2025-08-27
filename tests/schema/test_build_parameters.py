import pytest

from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.schema import BuildParameters

# -------------------------------
# Parsing / validation tests
# -------------------------------

def test_create_default_returns_quantities():
    params = BuildParameters.create_default()
    assert isinstance(params.beam_diameter, Quantity)
    assert params.beam_diameter.magnitude == 5e-5
    assert str(params.beam_diameter.units) == "meter"
    assert params.beam_power.magnitude == 200
    assert str(params.beam_power.units) == "watt"
    assert params.scan_velocity.magnitude == 0.8
    assert str(params.scan_velocity.units) == "meter / second"
    assert params.temperature_preheat.magnitude == 300
    assert str(params.temperature_preheat.units) == "kelvin"

def test_valid_build_parameters_parsing():
    data = {
        "beam_diameter": Quantity(1e-4, "meter"),
        "beam_power": Quantity(250, "watts"),
        "scan_velocity": Quantity(1.0, "meter / second"),
        "temperature_preheat": Quantity(350, "kelvin"),
    }
    params = BuildParameters(**data)
    for key, value in data.items():
        q = getattr(params, key)
        assert isinstance(q, Quantity)
        assert q.magnitude == value.magnitude
        assert str(q.units) == str(value.units)

def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        BuildParameters(
            beam_diameter="not_a_quantity",
            beam_power=Quantity(200, "watts"),
            scan_velocity=Quantity(1.0, "meter / second"),
            temperature_preheat=Quantity(300, "kelvin")
        )

# -------------------------------
# Serialization tests
# -------------------------------

def test_build_parameters_to_dict():
    build_parameters = BuildParameters.create_default()
    print(build_parameters)
    serialized = build_parameters.to_dict()
    for field in ["beam_diameter", "beam_power", "scan_velocity", "temperature_preheat"]:
        q_dict = serialized[field]
        q = getattr(build_parameters, field)
        assert q_dict["magnitude"] == q.magnitude
        assert q_dict["units"] == str(q.units)

# -------------------------------
# Save / load tests
# -------------------------------

def test_save_and_load(tmp_path: Path):
    params = BuildParameters.create_default()
    path = tmp_path / "params.json"
    saved_path = params.save(path)
    assert saved_path.exists()

    loaded_params = BuildParameters.load(saved_path)
    for field in ["beam_diameter", "beam_power", "scan_velocity", "temperature_preheat"]:
        original = getattr(params, field)
        loaded = getattr(loaded_params, field)
        assert loaded.magnitude == original.magnitude
        assert str(loaded.units) == str(original.units)
