import pytest
from pathlib import Path
from am.schema import QuantityModel
from pydantic import ValidationError
from pint import Quantity

# -----------------------------------
# Child models for testing
# -----------------------------------


class ChildModel(QuantityModel):
    _quantity_fields = {"length", "width"}

    length: Quantity
    width: Quantity
    id: int  # Non-quantity field


class ChildModelWithDefaults(QuantityModel):
    _quantity_fields = {"length"}
    _quantity_defaults = {"length": (1.0, "m")}

    length: Quantity
    id: int


# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_valid_quantity_parsing():
    data = {"length": Quantity(1.0, "m"), "width": Quantity(2.0, "m"), "id": 42}
    model = ChildModel(**data)
    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 1.0
    assert model.width.magnitude == 2.0
    assert model.id == 42


def test_invalid_magnitude_type_raises():
    with pytest.raises(ValidationError):
        ChildModel(length="not_a_quantity", width=Quantity(2.0, "m"), id=1)


def test_invalid_units_type_raises():
    with pytest.raises(TypeError):
        ChildModel(length=Quantity(1.0, 123), width=Quantity(2.0, "m"), id=1)


# Dict parsing
def test_parse_from_valid_dict():
    data = {
        "length": {"magnitude": 3.0, "units": "m"},
        "width": {"magnitude": 4, "units": "m"},
        "id": 99,
    }
    model = ChildModel(**data)
    assert model.length.magnitude == 3.0
    assert str(model.length.units) == "meter"


def test_parse_from_invalid_dict_keys():
    bad_data = {
        "length": {"mag": 3.0, "unit": "m"},  # wrong keys
        "width": {"magnitude": 2.0, "units": "m"},
        "id": 1,
    }
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


# Tuple parsing
def test_parse_from_valid_tuple():
    data = {"length": (5.0, "m"), "width": (6, "m"), "id": 10}
    model = ChildModel(**data)
    assert model.length.magnitude == 5.0
    assert str(model.width.units) == "meter"


def test_parse_from_invalid_tuple_length():
    bad_data = {"length": (5.0, "m", "extra"), "width": (6.0, "m"), "id": 2}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


def test_parse_from_invalid_tuple_types():
    bad_data = {"length": ("not_a_number", "m"), "width": (2.0, "m"), "id": 3}
    with pytest.raises(ValidationError):
        ChildModel(**bad_data)


# Bare float/int parsing
def test_parse_from_float_with_default_units():
    model = ChildModelWithDefaults(length=10.0, id=1)
    assert model.length.magnitude == 10.0
    assert str(model.length.units) == "meter"


def test_parse_from_float_without_default_units_raises():
    with pytest.raises(ValidationError):
        ChildModel(length=10.0, width=Quantity(2.0, "m"), id=1)


# -------------------------------
# Serialization tests
# -------------------------------


def test_serialize_model_returns_dict():
    data = {"length": Quantity(1.0, "m"), "width": Quantity(2.0, "m"), "id": 42}
    model = ChildModel(**data)
    serialized = model.serialize_model(lambda m: m.model_dump())
    assert serialized["length"]["magnitude"] == 1.0
    assert serialized["length"]["units"] == "meter"
    assert serialized["width"]["magnitude"] == 2.0
    assert serialized["width"]["units"] == "meter"
    assert serialized["id"] == 42


def test_to_dict_matches_model_dump():
    data = {"length": Quantity(5.0, "m"), "width": Quantity(6.0, "m"), "id": 7}
    model = ChildModel(**data)
    d = model.to_dict()
    assert d["length"]["magnitude"] == 5.0
    assert d["length"]["units"] == "meter"
    assert d["width"]["magnitude"] == 6.0
    assert d["width"]["units"] == "meter"
    assert d["id"] == 7


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load(tmp_path: Path):
    data = {"length": Quantity(1.1, "m"), "width": Quantity(2.2, "m"), "id": 123}
    model = ChildModel(**data)
    path = tmp_path / "test.json"
    saved_path = model.save(path)
    assert saved_path.exists()

    loaded_model = ChildModel.load(saved_path)
    assert loaded_model.length.magnitude == 1.1
    assert loaded_model.length.units == "meter"
    assert loaded_model.width.magnitude == 2.2
    assert loaded_model.width.units == "meter"
    assert loaded_model.id == 123


def test_round_trip_serialization(tmp_path: Path):
    original = ChildModel(length=Quantity(7, "m"), width=Quantity(8, "m"), id=55)
    path = tmp_path / "roundtrip.json"
    original.save(path)
    reloaded = ChildModel.load(path)
    assert reloaded.length == original.length
    assert reloaded.width == original.width
    assert reloaded.id == original.id
