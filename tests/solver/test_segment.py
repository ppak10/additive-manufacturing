import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.simulator.models import SolverSegment

# -------------------------------
# Parsing / validation tests
# -------------------------------


def test_valid_segment_parsing_from_quantity():
    """Test creating a Segment with Quantity objects."""
    data = {
        "x": Quantity(0.0, "millimeter"),
        "y": Quantity(0.0, "millimeter"),
        "z": Quantity(0.0, "millimeter"),
        "e": Quantity(0.0, "millimeter"),
        "x_next": Quantity(1.0, "millimeter"),
        "y_next": Quantity(0.5, "millimeter"),
        "z_next": Quantity(0.0, "millimeter"),
        "e_next": Quantity(0.1, "millimeter"),
        "angle_xy": Quantity(45.0, "degree"),
        "distance_xy": Quantity(1.118, "millimeter"),
        "travel": False,
    }
    segment = SolverSegment(**data)

    # Check all quantity fields
    for key, value in data.items():
        if key != "travel":
            q = getattr(segment, key)
            assert isinstance(q, Quantity)
            assert q.magnitude == value.magnitude
            assert str(q.units) == str(value.units)

    # Check boolean field
    assert segment.travel == False


def test_valid_segment_parsing_from_tuple():
    """(magnitude, unit) tuples should work for all quantity fields."""
    data = {
        "x": (0.0, "meter"),
        "y": (0.0, "meter"),
        "z": (0.0, "meter"),
        "e": (0.0, "meter"),
        "x_next": (0.001, "meter"),
        "y_next": (0.0005, "meter"),
        "z_next": (0.0, "meter"),
        "e_next": (0.0001, "meter"),
        "angle_xy": (0.785, "radian"),
        "distance_xy": (0.001118, "meter"),
        "travel": True,
    }
    segment = SolverSegment(**data)

    # Check units match what was provided
    assert str(segment.x.units) == "meter"
    assert str(segment.y.units) == "meter"
    assert str(segment.z.units) == "meter"
    assert str(segment.e.units) == "meter"
    assert str(segment.x_next.units) == "meter"
    assert str(segment.y_next.units) == "meter"
    assert str(segment.z_next.units) == "meter"
    assert str(segment.e_next.units) == "meter"
    assert str(segment.angle_xy.units) == "radian"
    assert str(segment.distance_xy.units) == "meter"
    assert segment.travel == True


def test_segment_with_different_units():
    """Test that different unit systems work correctly."""
    data = {
        "x": Quantity(10.0, "millimeter"),
        "y": Quantity(1.0, "centimeter"),
        "z": Quantity(0.001, "meter"),
        "e": Quantity(100.0, "micrometer"),
        "x_next": Quantity(20.0, "millimeter"),
        "y_next": Quantity(2.0, "centimeter"),
        "z_next": Quantity(0.002, "meter"),
        "e_next": Quantity(200.0, "micrometer"),
        "angle_xy": Quantity(90.0, "degree"),
        "distance_xy": Quantity(14.142, "millimeter"),
        "travel": False,
    }
    segment = SolverSegment(**data)

    # Verify each field has the correct magnitude and units
    assert segment.x.magnitude == 10.0
    assert str(segment.x.units) == "millimeter"
    assert segment.y.magnitude == 1.0
    assert str(segment.y.units) == "centimeter"
    assert segment.z.magnitude == 0.001
    assert str(segment.z.units) == "meter"


def test_invalid_type_raises():
    """Invalid types should raise ValidationError."""
    with pytest.raises(ValidationError):
        SolverSegment(
            x="not_a_quantity",  # Invalid type
            y=Quantity(0.0, "millimeter"),
            z=Quantity(0.0, "millimeter"),
            e=Quantity(0.0, "millimeter"),
            x_next=Quantity(1.0, "millimeter"),
            y_next=Quantity(0.5, "millimeter"),
            z_next=Quantity(0.0, "millimeter"),
            e_next=Quantity(0.1, "millimeter"),
            angle_xy=Quantity(45.0, "degree"),
            distance_xy=Quantity(1.118, "millimeter"),
            travel=False,
        )


def test_missing_required_field_raises():
    """Missing required fields should raise ValidationError."""
    with pytest.raises(ValidationError):
        SolverSegment(
            x=Quantity(0.0, "millimeter"),
            y=Quantity(0.0, "millimeter"),
            # Missing z and other required fields
        )


def test_invalid_travel_type_raises():
    """travel field must be a boolean."""
    with pytest.raises(ValidationError):
        SolverSegment(
            x=Quantity(0.0, "millimeter"),
            y=Quantity(0.0, "millimeter"),
            z=Quantity(0.0, "millimeter"),
            e=Quantity(0.0, "millimeter"),
            x_next=Quantity(1.0, "millimeter"),
            y_next=Quantity(0.5, "millimeter"),
            z_next=Quantity(0.0, "millimeter"),
            e_next=Quantity(0.1, "millimeter"),
            angle_xy=Quantity(45.0, "degree"),
            distance_xy=Quantity(1.118, "millimeter"),
            travel="not_a_bool",  # Invalid type
        )


# -------------------------------
# Serialization tests
# -------------------------------


def test_segment_to_dict():
    """Test serialization to dictionary."""
    segment = SolverSegment(
        x=Quantity(0.0, "millimeter"),
        y=Quantity(0.0, "millimeter"),
        z=Quantity(0.0, "millimeter"),
        e=Quantity(0.0, "millimeter"),
        x_next=Quantity(1.0, "millimeter"),
        y_next=Quantity(0.5, "millimeter"),
        z_next=Quantity(0.0, "millimeter"),
        e_next=Quantity(0.1, "millimeter"),
        angle_xy=Quantity(45.0, "degree"),
        distance_xy=Quantity(1.118, "millimeter"),
        travel=False,
    )

    serialized = segment.to_dict()

    # Check quantity fields are properly serialized
    for field in [
        "x",
        "y",
        "z",
        "e",
        "x_next",
        "y_next",
        "z_next",
        "e_next",
        "angle_xy",
        "distance_xy",
    ]:
        q_dict = serialized[field]
        q = getattr(segment, field)
        assert q_dict["magnitude"] == q.magnitude
        assert q_dict["units"] == str(q.units)

    # Check boolean field
    assert serialized["travel"] == False


# -------------------------------
# Save / load tests
# -------------------------------


def test_save_and_load(tmp_path: Path):
    """Test saving to JSON and loading back."""
    segment = SolverSegment(
        x=Quantity(5.0, "millimeter"),
        y=Quantity(10.0, "millimeter"),
        z=Quantity(0.1, "millimeter"),
        e=Quantity(0.05, "millimeter"),
        x_next=Quantity(6.0, "millimeter"),
        y_next=Quantity(11.0, "millimeter"),
        z_next=Quantity(0.1, "millimeter"),
        e_next=Quantity(0.06, "millimeter"),
        angle_xy=Quantity(30.0, "degree"),
        distance_xy=Quantity(1.414, "millimeter"),
        travel=True,
    )

    path = tmp_path / "segment.json"
    saved_path = segment.save(path)
    assert saved_path.exists()

    loaded_segment = SolverSegment.load(saved_path)

    # Verify all quantity fields are preserved
    for field in [
        "x",
        "y",
        "z",
        "e",
        "x_next",
        "y_next",
        "z_next",
        "e_next",
        "angle_xy",
        "distance_xy",
    ]:
        original = getattr(segment, field)
        loaded = getattr(loaded_segment, field)
        assert loaded.magnitude == original.magnitude
        assert str(loaded.units) == str(original.units)

    # Verify boolean field is preserved
    assert loaded_segment.travel == segment.travel


def test_save_and_load_with_different_units(tmp_path: Path):
    """Test that units are preserved through save/load cycle."""
    segment = SolverSegment(
        x=Quantity(5000.0, "micrometer"),
        y=Quantity(1.0, "centimeter"),
        z=Quantity(0.0001, "meter"),
        e=Quantity(50.0, "micrometer"),
        x_next=Quantity(6000.0, "micrometer"),
        y_next=Quantity(1.1, "centimeter"),
        z_next=Quantity(0.0001, "meter"),
        e_next=Quantity(60.0, "micrometer"),
        angle_xy=Quantity(1.571, "radian"),
        distance_xy=Quantity(0.001414, "meter"),
        travel=False,
    )

    path = tmp_path / "segment_units.json"
    saved_path = segment.save(path)
    loaded_segment = SolverSegment.load(saved_path)

    # Verify units are exactly preserved
    assert str(loaded_segment.x.units) == str(segment.x.units)
    assert str(loaded_segment.angle_xy.units) == str(segment.angle_xy.units)
    assert loaded_segment.x.magnitude == segment.x.magnitude
