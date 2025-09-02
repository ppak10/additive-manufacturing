import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.schema.material import Material

# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_create_default_returns_quantities():
    material = Material()
    assert material.name == "Stainless Steel 316L"
    assert isinstance(material.specific_heat_capacity, Quantity)
    assert material.specific_heat_capacity.magnitude == 455
    assert str(material.specific_heat_capacity.units) == "joule / kelvin / kilogram"
    assert material.absorptivity.magnitude == 1.0
    assert str(material.absorptivity.units) == "dimensionless"
    assert material.thermal_conductivity.magnitude == 8.9
    assert str(material.thermal_conductivity.units) == "watt / kelvin / meter"
    assert material.density.magnitude == 7910
    assert str(material.density.units) == "kilogram / meter ** 3"
    assert material.temperature_melt.magnitude == 1673
    assert str(material.temperature_melt.units) == "kelvin"
    assert material.temperature_liquidus.magnitude == 1710.26
    assert str(material.temperature_liquidus.units) == "kelvin"
    assert material.temperature_solidus.magnitude == 1683.68
    assert str(material.temperature_solidus.units) == "kelvin"


def test_valid_material_parsing_from_quantity():
    data = {
        "name": "Custom Material",
        "specific_heat_capacity": Quantity(500, "joule / (kilogram * kelvin)"),
        "absorptivity": Quantity(0.8, "dimensionless"),
        "thermal_conductivity": Quantity(10.5, "watt / (meter * kelvin)"),
        "density": Quantity(8000, "kilogram / meter ** 3"),
        "temperature_melt": Quantity(1700, "kelvin"),
        "temperature_liquidus": Quantity(1750, "kelvin"),
        "temperature_solidus": Quantity(1720, "kelvin"),
    }
    material = Material(**data)
    assert material.name == "Custom Material"
    for key, value in data.items():
        if key != "name":
            q = getattr(material, key)
            assert isinstance(q, Quantity)
            assert q.magnitude == value.magnitude
            assert str(q.units) == str(value.units)


def test_valid_material_parsing_from_float_defaults():
    """Passing only numbers should use default units from _quantity_defaults."""
    data = {
        "specific_heat_capacity": 500,
        "absorptivity": 0.8,
        "thermal_conductivity": 10.5,
        "density": 8000,
        "temperature_melt": 1700,
        "temperature_liquidus": 1750,
        "temperature_solidus": 1720,
    }
    material = Material(**data)
    assert str(material.specific_heat_capacity.units) == "joule / kelvin / kilogram"
    assert str(material.absorptivity.units) == "dimensionless"
    assert str(material.thermal_conductivity.units) == "watt / kelvin / meter"
    assert str(material.density.units) == "kilogram / meter ** 3"
    assert str(material.temperature_melt.units) == "kelvin"
    assert str(material.temperature_liquidus.units) == "kelvin"
    assert str(material.temperature_solidus.units) == "kelvin"


def test_valid_material_parsing_from_tuple():
    """(magnitude, unit) tuples should override default units."""
    data = {
        "specific_heat_capacity": (500, "kilojoule / (kilogram * kelvin)"),
        "absorptivity": (0.8, "dimensionless"),
        "thermal_conductivity": (10.5, "milliwatt / (millimeter * kelvin)"),
        "density": (7.91, "gram / centimeter ** 3"),
        "temperature_melt": (1673, "celsius"),
        "temperature_liquidus": (1710.26, "fahrenheit"),
        "temperature_solidus": (1683.68, "rankine"),
    }
    material = Material(**data)
    assert str(material.specific_heat_capacity.units) == "kilojoule / kelvin / kilogram"
    assert str(material.absorptivity.units) == "dimensionless"
    assert str(material.thermal_conductivity.units) == "milliwatt / kelvin / millimeter"
    assert str(material.density.units) == "gram / centimeter ** 3"
    assert str(material.temperature_melt.units) == "degree_Celsius"
    assert str(material.temperature_liquidus.units) == "degree_Fahrenheit"
    assert str(material.temperature_solidus.units) == "degree_Rankine"


def test_invalid_type_raises():
    with pytest.raises(ValidationError):
        Material(
            specific_heat_capacity="not_a_quantity",
            absorptivity=Quantity(1.0, "dimensionless"),
            thermal_conductivity=Quantity(8.9, "watt / (meter * kelvin)"),
            density=Quantity(7910, "kilogram / meter ** 3"),
        )


# -------------------------------
# Serialization tests
# -------------------------------


def test_material_to_dict():
    material = Material()
    serialized = material.to_dict()
    assert serialized["name"] == "Stainless Steel 316L"
    for field in [
        "specific_heat_capacity",
        "absorptivity",
        "thermal_conductivity",
        "density",
        "temperature_melt",
        "temperature_liquidus",
        "temperature_solidus",
    ]:
        q_dict = serialized[field]
        q = getattr(material, field)
        assert q_dict["magnitude"] == q.magnitude
        assert q_dict["units"] == str(q.units)


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load(tmp_path: Path):
    material = Material()
    path = tmp_path / "material.json"
    saved_path = material.save(path)
    assert saved_path.exists()

    loaded_material = Material.load(saved_path)
    assert loaded_material.name == material.name
    for field in [
        "specific_heat_capacity",
        "absorptivity",
        "thermal_conductivity",
        "density",
        "temperature_melt",
        "temperature_liquidus",
        "temperature_solidus",
    ]:
        original = getattr(material, field)
        loaded = getattr(loaded_material, field)
        assert loaded.magnitude == original.magnitude
        assert str(loaded.units) == str(original.units)
