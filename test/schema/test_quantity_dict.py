from am.schema import QuantityDict

def test_valid_quantity_dict_with_float():
    q: QuantityDict = {"magnitude": 1.23, "units": "m"}
    assert isinstance(q["magnitude"], float)
    assert q["magnitude"] == 1.23
    assert q["units"] == "m"

def test_valid_quantity_dict_with_int():
    q: QuantityDict = {"magnitude": 5, "units": "s"}
    assert isinstance(q["magnitude"], int)
    assert q["magnitude"] == 5
    assert q["units"] == "s"

def test_invalid_magnitude_type():
    q: QuantityDict = {"magnitude": "not_a_number", "units": "m"}
    # Validate manually since TypedDict doesn't enforce types
    assert isinstance(q["magnitude"], str)
    assert not isinstance(q["magnitude"], (int, float))

def test_invalid_units_type():
    q: QuantityDict = {"magnitude": 1.0, "units": 123}
    assert isinstance(q["units"], int)
    assert not isinstance(q["units"], str)

def test_missing_keys():
    # Missing magnitude
    q: dict = {"units": "m"}
    assert "magnitude" not in q
    # Missing units
    q: dict = {"magnitude": 10}
    assert "units" not in q


