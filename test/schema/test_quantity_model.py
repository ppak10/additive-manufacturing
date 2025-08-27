import pytest
from pathlib import Path
from am.schema import QuantityModel
from pydantic import ValidationError
from pint import Quantity

class ChildModel(QuantityModel):
    _quantity_fields = {"length", "width"}

    length: Quantity
    width: Quantity

    id: int  # Non-quantity field

# -------------------------------
# Parsing / validation tests
# -------------------------------

def test_valid_quantity_parsing():
    data = {
        "length": Quantity(1.0, "m"),
        "width": Quantity(2.0, "m"),
        "id": 42
    }
    model = ChildModel(**data)
    assert isinstance(model.length, Quantity)
    assert model.length.magnitude == 1.0
    assert model.width.magnitude == 2.0
    assert model.id == 42

def test_invalid_magnitude_type_raises():
    with pytest.raises(ValidationError):
        # Can't pass a string as a Quantity
        ChildModel(length="not_a_quantity", width=Quantity(2.0, "m"), id=1)

def test_invalid_units_type_raises():
    with pytest.raises(TypeError):
        # Invalid units type
        ChildModel(length=Quantity(1.0, 123), width=Quantity(2.0, "m"), id=1)

# -------------------------------
# Serialization tests
# -------------------------------

def test_serialize_model_returns_dict():
    data = {
        "length": Quantity(1.0, "m"),
        "width": Quantity(2.0, "m"),
        "id": 42
    }
    model = ChildModel(**data)
    serialized = model.serialize_model(lambda m: m.model_dump())
    assert serialized["length"]["magnitude"] == 1.0
    assert serialized["length"]["units"] == "meter"
    assert serialized["width"]["magnitude"] == 2.0
    assert serialized["width"]["units"] == "meter"
    assert serialized["id"] == 42

def test_to_dict_matches_model_dump():
    data = {
        "length": Quantity(5.0, "m"),
        "width": Quantity(6.0, "m"),
        "id": 7
    }
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
    data = {
        "length": Quantity(1.1, "m"),
        "width": Quantity(2.2, "m"),
        "id": 123
    }
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

