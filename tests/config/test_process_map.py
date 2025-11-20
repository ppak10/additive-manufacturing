import pytest
from pint import Quantity
from pydantic import ValidationError

from am.config.process_map import ProcessMap, ProcessMapDict

# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_create_default_empty_process_map():
    """Test creating a ProcessMap with default empty lists."""
    process_map = ProcessMap()
    assert process_map.parameters == []
    assert process_map.points == []


def test_create_process_map_with_parameters_and_points():
    """Test creating a ProcessMap with parameters and points."""
    parameters = ["beam_power", "scan_velocity"]
    points = [
        [Quantity(100, "watt"), Quantity(0.5, "meter / second")],
        [Quantity(200, "watt"), Quantity(0.8, "meter / second")],
        [Quantity(300, "watt"), Quantity(1.0, "meter / second")],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)

    assert process_map.parameters == parameters
    assert len(process_map.points) == 3
    assert isinstance(process_map.points[0][0], Quantity)
    assert process_map.points[0][0].magnitude == 100
    assert str(process_map.points[0][0].units) == "watt"
    assert process_map.points[1][1].magnitude == 0.8
    assert str(process_map.points[1][1].units) == "meter / second"


def test_create_process_map_with_single_parameter():
    """Test creating a ProcessMap with a single parameter."""
    parameters = ["temperature_preheat"]
    points = [
        [Quantity(300, "kelvin")],
        [Quantity(400, "kelvin")],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)

    assert len(process_map.parameters) == 1
    assert len(process_map.points) == 2
    assert process_map.points[0][0].magnitude == 300


def test_create_process_map_with_multiple_parameters():
    """Test creating a ProcessMap with multiple parameters (up to MAX_PARAMETERS=3)."""
    parameters = ["beam_power", "scan_velocity", "hatch_spacing"]
    points = [
        [
            Quantity(150, "watt"),
            Quantity(0.6, "meter / second"),
            Quantity(50, "micrometer"),
        ],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)

    assert len(process_map.parameters) == 3
    assert len(process_map.points[0]) == 3
    assert process_map.points[0][2].magnitude == 50
    assert str(process_map.points[0][2].units) == "micrometer"


# -------------------------------
# Serialization tests
# -------------------------------


def test_process_map_serialization_empty():
    """Test serialization of an empty ProcessMap."""
    process_map = ProcessMap()
    serialized = process_map.model_dump()

    assert serialized["parameters"] == []
    assert serialized["points"] == []


def test_process_map_serialization_with_data():
    """Test serialization converts Quantity objects to dicts."""
    parameters = ["beam_power", "scan_velocity"]
    points = [
        [Quantity(100, "watt"), Quantity(0.5, "meter / second")],
        [Quantity(200, "watt"), Quantity(0.8, "meter / second")],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)
    serialized = process_map.model_dump()

    assert serialized["parameters"] == ["beam_power", "scan_velocity"]
    assert len(serialized["points"]) == 2

    # Check first point
    assert "beam_power" in serialized["points"][0]
    assert "scan_velocity" in serialized["points"][0]
    assert serialized["points"][0]["beam_power"]["magnitude"] == 100
    assert serialized["points"][0]["beam_power"]["units"] == "watt"
    assert serialized["points"][0]["scan_velocity"]["magnitude"] == 0.5
    assert serialized["points"][0]["scan_velocity"]["units"] == "meter / second"

    # Check second point
    assert serialized["points"][1]["beam_power"]["magnitude"] == 200
    assert serialized["points"][1]["scan_velocity"]["magnitude"] == 0.8


def test_process_map_serialization_structure():
    """Test that serialized data matches ProcessMapDict structure."""
    parameters = ["beam_power"]
    points = [[Quantity(150, "watt")]]

    process_map = ProcessMap(parameters=parameters, points=points)
    serialized = process_map.model_dump()

    # Verify structure matches ProcessMapDict TypedDict
    assert isinstance(serialized["parameters"], list)
    assert isinstance(serialized["points"], list)
    assert isinstance(serialized["points"][0], dict)
    assert isinstance(serialized["points"][0]["beam_power"], dict)
    assert "magnitude" in serialized["points"][0]["beam_power"]
    assert "units" in serialized["points"][0]["beam_power"]


# -------------------------------
# Deserialization tests (from_dict)
# -------------------------------


def test_from_dict_empty():
    """Test from_dict with empty parameters and points."""
    data = {"parameters": [], "points": []}
    process_map = ProcessMap.from_dict(data)

    assert process_map.parameters == []
    assert process_map.points == []


def test_from_dict_with_data():
    """Test from_dict converts serialized dicts back to Quantity objects."""
    data = {
        "parameters": ["beam_power", "scan_velocity"],
        "points": [
            {
                "beam_power": {"magnitude": 100, "units": "watt"},
                "scan_velocity": {"magnitude": 0.5, "units": "meter / second"},
            },
            {
                "beam_power": {"magnitude": 200, "units": "watt"},
                "scan_velocity": {"magnitude": 0.8, "units": "meter / second"},
            },
        ],
    }

    process_map = ProcessMap.from_dict(data)

    assert process_map.parameters == ["beam_power", "scan_velocity"]
    assert len(process_map.points) == 2

    # Check first point
    assert isinstance(process_map.points[0][0], Quantity)
    assert process_map.points[0][0].magnitude == 100
    assert str(process_map.points[0][0].units) == "watt"
    assert process_map.points[0][1].magnitude == 0.5

    # Check second point
    assert process_map.points[1][0].magnitude == 200
    assert process_map.points[1][1].magnitude == 0.8


def test_from_dict_missing_parameters():
    """Test from_dict when parameters key is missing."""
    data = {"points": []}
    process_map = ProcessMap.from_dict(data)

    assert process_map.parameters == []
    assert process_map.points == []


def test_from_dict_missing_points():
    """Test from_dict when points key is missing."""
    data = {"parameters": ["beam_power"]}
    process_map = ProcessMap.from_dict(data)

    assert process_map.parameters == ["beam_power"]
    assert process_map.points == []


def test_from_dict_partial_point():
    """Test from_dict when a point is missing some parameters."""
    data = {
        "parameters": ["beam_power", "scan_velocity"],
        "points": [
            {
                "beam_power": {"magnitude": 100, "units": "watt"},
                # scan_velocity is missing
            },
        ],
    }

    process_map = ProcessMap.from_dict(data)

    assert len(process_map.points) == 1
    # Only beam_power should be in the point
    assert len(process_map.points[0]) == 1
    assert process_map.points[0][0].magnitude == 100


# -------------------------------
# Round-trip tests
# -------------------------------


def test_serialization_deserialization_round_trip():
    """Test that serialization followed by deserialization preserves data."""
    parameters = ["beam_power", "scan_velocity", "hatch_spacing"]
    points = [
        [
            Quantity(100, "watt"),
            Quantity(0.5, "meter / second"),
            Quantity(50, "micrometer"),
        ],
        [
            Quantity(200, "watt"),
            Quantity(0.8, "meter / second"),
            Quantity(75, "micrometer"),
        ],
    ]

    original = ProcessMap(parameters=parameters, points=points)
    serialized = original.model_dump()
    restored = ProcessMap.from_dict(serialized)

    assert restored.parameters == original.parameters
    assert len(restored.points) == len(original.points)

    for i, point in enumerate(restored.points):
        for j, quantity in enumerate(point):
            assert quantity.magnitude == original.points[i][j].magnitude
            assert str(quantity.units) == str(original.points[i][j].units)


def test_multiple_round_trips():
    """Test that multiple serialization/deserialization cycles preserve data."""
    parameters = ["beam_power", "scan_velocity"]
    points = [
        [Quantity(150, "watt"), Quantity(0.6, "meter / second")],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)

    # Perform multiple round trips
    for _ in range(3):
        serialized = process_map.model_dump()
        process_map = ProcessMap.from_dict(serialized)

    assert process_map.parameters == parameters
    assert process_map.points[0][0].magnitude == 150
    assert process_map.points[0][1].magnitude == 0.6


# -------------------------------
# Edge case tests
# -------------------------------


def test_empty_parameters_with_points():
    """Test ProcessMap with points but no parameter names."""
    points = [
        [Quantity(100, "watt")],
    ]

    process_map = ProcessMap(parameters=[], points=points)

    assert process_map.parameters == []
    assert len(process_map.points) == 1


def test_parameters_without_points():
    """Test ProcessMap with parameter names but no points."""
    parameters = ["beam_power", "scan_velocity"]

    process_map = ProcessMap(parameters=parameters, points=[])

    assert len(process_map.parameters) == 2
    assert process_map.points == []


def test_different_units_for_same_parameter():
    """Test that points can have different units for the same parameter."""
    parameters = ["temperature"]
    points = [
        [Quantity(300, "kelvin")],
        [Quantity(100, "celsius")],
        [Quantity(500, "fahrenheit")],
    ]

    process_map = ProcessMap(parameters=parameters, points=points)
    serialized = process_map.model_dump()

    assert serialized["points"][0]["temperature"]["units"] == "kelvin"
    assert serialized["points"][1]["temperature"]["units"] == "degree_Celsius"
    assert serialized["points"][2]["temperature"]["units"] == "degree_Fahrenheit"


# -------------------------------
# Parameter ranges tests
# -------------------------------


def test_create_process_map_from_single_parameter_range():
    """Test creating a ProcessMap from a single parameter range."""
    parameter_ranges = [{"beam_power": ([100, "watt"], [300, "watt"], [100, "watt"])}]

    process_map = ProcessMap(parameter_ranges=parameter_ranges)

    assert process_map.parameters == ["beam_power"]
    assert len(process_map.points) == 3  # 100, 200, 300
    assert process_map.points[0][0].magnitude == 100
    assert process_map.points[1][0].magnitude == 200
    assert process_map.points[2][0].magnitude == 300
    assert all(str(p[0].units) == "watt" for p in process_map.points)


def test_create_process_map_from_two_parameter_ranges():
    """Test creating a ProcessMap from two parameter ranges (Cartesian product)."""
    parameter_ranges = [
        {"beam_power": ([100, "watt"], [200, "watt"], [100, "watt"])},
        {
            "scan_velocity": (
                [0.5, "meter / second"],
                [1.0, "meter / second"],
                [0.25, "meter / second"],
            )
        },
    ]

    process_map = ProcessMap(parameter_ranges=parameter_ranges)

    assert process_map.parameters == ["beam_power", "scan_velocity"]
    # Should have 2 power values × 3 velocity values = 6 points
    assert len(process_map.points) == 6

    # Verify first point
    assert process_map.points[0][0].magnitude == 100  # beam_power
    assert process_map.points[0][1].magnitude == 0.5  # scan_velocity

    # Verify last point
    assert process_map.points[-1][0].magnitude == 200  # beam_power
    assert process_map.points[-1][1].magnitude == 1.0  # scan_velocity


def test_parameter_ranges_not_stored_in_model():
    """Test that parameter_ranges is not stored in the model after initialization."""
    parameter_ranges = [{"beam_power": ([100, "watt"], [200, "watt"], [100, "watt"])}]

    process_map = ProcessMap(parameter_ranges=parameter_ranges)

    # parameter_ranges should not be an attribute
    assert not hasattr(process_map, "parameter_ranges")

    # Serialization should not include parameter_ranges
    serialized = process_map.model_dump()
    assert "parameter_ranges" not in serialized
    assert "parameters" in serialized
    assert "points" in serialized


def test_parameter_ranges_serialization_round_trip():
    """Test that ProcessMap created from parameter_ranges can be serialized and deserialized."""
    parameter_ranges = [
        {"beam_power": ([100, "watt"], [200, "watt"], [100, "watt"])},
        {"scan_velocity": ([0.5, "m/s"], [1.0, "m/s"], [0.5, "m/s"])},
    ]

    original = ProcessMap(parameter_ranges=parameter_ranges)
    serialized = original.model_dump()
    restored = ProcessMap.from_dict(serialized)

    assert restored.parameters == original.parameters
    assert len(restored.points) == len(original.points)

    for i, point in enumerate(restored.points):
        for j, quantity in enumerate(point):
            assert quantity.magnitude == original.points[i][j].magnitude


def test_empty_parameter_ranges():
    """Test creating a ProcessMap with empty parameter_ranges."""
    process_map = ProcessMap(parameter_ranges=[])

    assert process_map.parameters == []
    assert process_map.points == []


def test_parameter_ranges_with_none():
    """Test creating a ProcessMap with parameter_ranges=None."""
    process_map = ProcessMap(parameter_ranges=None)

    assert process_map.parameters == []
    assert process_map.points == []


def test_parameter_ranges_exceeds_max():
    """Test that exceeding MAX_PARAMETERS with parameter_ranges raises an error."""
    parameter_ranges = [
        {"param1": ([0, "watt"], [1, "watt"], [1, "watt"])},
        {"param2": ([0, "watt"], [1, "watt"], [1, "watt"])},
        {"param3": ([0, "watt"], [1, "watt"], [1, "watt"])},
        {"param4": ([0, "watt"], [1, "watt"], [1, "watt"])},  # Exceeds MAX of 3
    ]

    with pytest.raises(ValidationError):
        ProcessMap(parameter_ranges=parameter_ranges)


def test_direct_parameters_exceeds_max():
    """Test that exceeding MAX_PARAMETERS with direct parameters raises an error."""
    parameters = ["beam_power", "scan_velocity", "hatch_spacing", "layer_height"]
    points = [
        [
            Quantity(150, "watt"),
            Quantity(0.6, "meter / second"),
            Quantity(50, "micrometer"),
            Quantity(100, "micrometer"),
        ],
    ]

    with pytest.raises(ValidationError):
        ProcessMap(parameters=parameters, points=points)
