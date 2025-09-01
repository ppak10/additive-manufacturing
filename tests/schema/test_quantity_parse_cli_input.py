import pytest
from am.schema import parse_cli_input


@pytest.mark.parametrize(
    "inp, expected",
    [
        # plain string numbers
        ("5", 5.0),
        ("42", 42.0),
        ("3.14", 3.14),
    ],
)
def test_valid_plain_number_inputs(inp, expected):
    """Check that valid inputs parse into magnitude + units."""
    result = parse_cli_input(inp)
    assert isinstance(result, float | int)
    assert pytest.approx(result) == expected
    assert result == expected


@pytest.mark.parametrize(
    "inp, expected",
    [
        # numbers with units (space separated)
        ("5 meter", (5.0, "meter")),
        ("1.1 m/s", (1.1, "m/s")),
        ("200 watts", (200.0, "watts")),
        # tuple-style inputs
        ("(5e-5, 'meter')", (5e-5, "meter")),
        ("(200, 'watts')", (200.0, "watts")),
        # scientific notation with space unit
        ("5e-5 meter", (5e-5, "meter")),
        # no parentheses
        ("1.0, meter", (1.0, "meter")),
        # no parentheses, no space
        ("1.0,meter", (1.0, "meter")),
    ],
)
def test_valid_magnitude_and_units_inputs(inp, expected):
    """Check that valid inputs parse into magnitude + units."""
    result = parse_cli_input(inp)
    assert isinstance(result, tuple)
    assert pytest.approx(result[0]) == expected[0]
    assert result[1] == expected[1]


@pytest.mark.parametrize(
    "inp",
    [
        # plain numbers
        5,
        42,
        3.14,
    ],
)
def test_unsupported_types(inp):
    """Check that invalid inputs raise ValueError."""
    with pytest.raises(TypeError):
        parse_cli_input(inp)


@pytest.mark.parametrize(
    "inp",
    [
        "",  # empty
        "foobar",  # invalid string
        "(1.0,)",  # tuple missing units
        "(, 'meter')",  # tuple missing magnitude
        "(5e-5 'meter')",  # missing comma
    ],
)
def test_invalid_inputs(inp):
    """Check that invalid inputs raise ValueError."""
    with pytest.raises(ValueError):
        parse_cli_input(inp)
