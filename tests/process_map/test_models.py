import pytest
from pathlib import Path
from pint import Quantity
from pydantic import ValidationError

from am.config import BuildParameters
from am.solver.types import MeltPoolDimensions
from am.process_map.models import (
    MeltPoolClassifications,
    ProcessMapPoint,
    ProcessMapPoints,
)

# -------------------------------
# MeltPoolClassifications tests
# -------------------------------


def test_melt_pool_classifications_default_values():
    """Test that all fields default to None."""
    classifications = MeltPoolClassifications()
    assert classifications.lack_of_fusion is None
    assert classifications.keyholing is None
    assert classifications.balling is None


def test_melt_pool_classifications_with_all_true():
    """Test creating classifications with all fields set to True."""
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=True,
        balling=True,
    )
    assert classifications.lack_of_fusion is True
    assert classifications.keyholing is True
    assert classifications.balling is True


def test_melt_pool_classifications_with_all_false():
    """Test creating classifications with all fields set to False."""
    classifications = MeltPoolClassifications(
        lack_of_fusion=False,
        keyholing=False,
        balling=False,
    )
    assert classifications.lack_of_fusion is False
    assert classifications.keyholing is False
    assert classifications.balling is False


def test_melt_pool_classifications_with_mixed_values():
    """Test creating classifications with mixed boolean and None values."""
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=None,
        balling=False,
    )
    assert classifications.lack_of_fusion is True
    assert classifications.keyholing is None
    assert classifications.balling is False


def test_melt_pool_classifications_partial_specification():
    """Test creating classifications with only some fields specified."""
    classifications = MeltPoolClassifications(lack_of_fusion=True)
    assert classifications.lack_of_fusion is True
    assert classifications.keyholing is None
    assert classifications.balling is None


def test_melt_pool_classifications_invalid_type():
    """Test that invalid types raise ValidationError."""
    with pytest.raises(ValidationError):
        MeltPoolClassifications(lack_of_fusion="invalid")


def test_melt_pool_classifications_serialization():
    """Test that MeltPoolClassifications can be serialized to dict."""
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=False,
        balling=None,
    )
    data = classifications.model_dump()
    assert data["lack_of_fusion"] is True
    assert data["keyholing"] is False
    assert data["balling"] is None


# -------------------------------
# ProcessMapPoint tests
# -------------------------------


def test_process_map_point_creation_with_valid_data():
    """Test creating a ProcessMapPoint with valid data."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100, "micrometer"),
        width=Quantity(80, "micrometer"),
        length=Quantity(150, "micrometer"),
        length_front=Quantity(60, "micrometer"),
        length_behind=Quantity(90, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=False,
        keyholing=False,
        balling=False,
    )

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    assert isinstance(point.build_parameters, BuildParameters)
    assert isinstance(point.melt_pool_dimensions, MeltPoolDimensions)
    assert isinstance(point.melt_pool_classifications, MeltPoolClassifications)
    assert point.melt_pool_classifications.lack_of_fusion is False


def test_process_map_point_with_custom_build_parameters():
    """Test ProcessMapPoint with custom build parameters."""
    build_params = BuildParameters(
        beam_power=Quantity(300, "watt"),
        scan_velocity=Quantity(1.2, "meter / second"),
    )
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(120, "micrometer"),
        width=Quantity(90, "micrometer"),
        length=Quantity(180, "micrometer"),
        length_front=Quantity(70, "micrometer"),
        length_behind=Quantity(110, "micrometer"),
    )
    classifications = MeltPoolClassifications()

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    assert point.build_parameters.beam_power.magnitude == 300
    assert str(point.build_parameters.beam_power.units) == "watt"
    assert point.build_parameters.scan_velocity.magnitude == 1.2


def test_process_map_point_with_defects():
    """Test ProcessMapPoint with various defect classifications."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(50, "micrometer"),
        width=Quantity(40, "micrometer"),
        length=Quantity(80, "micrometer"),
        length_front=Quantity(30, "micrometer"),
        length_behind=Quantity(50, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=False,
        balling=True,
    )

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    assert point.melt_pool_classifications.lack_of_fusion is True
    assert point.melt_pool_classifications.keyholing is False
    assert point.melt_pool_classifications.balling is True


def test_process_map_point_missing_required_field():
    """Test that missing required fields raise ValidationError."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100, "micrometer"),
        width=Quantity(80, "micrometer"),
        length=Quantity(150, "micrometer"),
        length_front=Quantity(60, "micrometer"),
        length_behind=Quantity(90, "micrometer"),
    )

    # Missing melt_pool_classifications
    with pytest.raises(ValidationError):
        ProcessMapPoint(
            build_parameters=build_params,
            melt_pool_dimensions=melt_pool_dims,
        )


def test_process_map_point_serialization():
    """Test that ProcessMapPoint can be serialized to dict."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100, "micrometer"),
        width=Quantity(80, "micrometer"),
        length=Quantity(150, "micrometer"),
        length_front=Quantity(60, "micrometer"),
        length_behind=Quantity(90, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=False,
        keyholing=True,
        balling=False,
    )

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    data = point.model_dump()
    assert "build_parameters" in data
    assert "melt_pool_dimensions" in data
    assert "melt_pool_classifications" in data
    assert data["melt_pool_classifications"]["keyholing"] is True


def test_process_map_point_to_dict():
    """Test that ProcessMapPoint to_dict() properly serializes all fields."""
    build_params = BuildParameters(
        beam_power=Quantity(275.0, "watt"),
        scan_velocity=Quantity(1.2, "meter / second"),
    )
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(115.0, "micrometer"),
        width=Quantity(88.0, "micrometer"),
        length=Quantity(165.0, "micrometer"),
        length_front=Quantity(68.0, "micrometer"),
        length_behind=Quantity(97.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=False,
        balling=True,
    )

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    data = point.to_dict()

    # Check structure
    assert "build_parameters" in data
    assert "melt_pool_dimensions" in data
    assert "melt_pool_classifications" in data

    # Check build parameters are properly serialized as QuantityDicts
    assert "beam_power" in data["build_parameters"]
    assert isinstance(data["build_parameters"]["beam_power"], dict)
    assert data["build_parameters"]["beam_power"]["magnitude"] == 275.0
    assert data["build_parameters"]["beam_power"]["units"] == "watt"

    # Check melt pool dimensions are properly serialized
    assert "depth" in data["melt_pool_dimensions"]
    assert isinstance(data["melt_pool_dimensions"]["depth"], dict)
    assert data["melt_pool_dimensions"]["depth"]["magnitude"] == 115.0
    assert data["melt_pool_dimensions"]["depth"]["units"] == "micrometer"

    # Check classifications
    assert data["melt_pool_classifications"]["lack_of_fusion"] is True
    assert data["melt_pool_classifications"]["keyholing"] is False
    assert data["melt_pool_classifications"]["balling"] is True


def test_process_map_point_from_dict():
    """Test creating ProcessMapPoint from dictionary data."""
    # Create initial point
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100.0, "micrometer"),
        width=Quantity(80.0, "micrometer"),
        length=Quantity(150.0, "micrometer"),
        length_front=Quantity(60.0, "micrometer"),
        length_behind=Quantity(90.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(lack_of_fusion=True)

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    # Serialize and deserialize
    data = point.model_dump()
    recreated_point = ProcessMapPoint(**data)

    assert recreated_point.melt_pool_classifications.lack_of_fusion is True
    assert (
        recreated_point.build_parameters.beam_power.magnitude
        == build_params.beam_power.magnitude
    )


# -------------------------------
# Save / load tests
# -------------------------------


def test_process_map_point_save_and_load(tmp_path: Path):
    """Test saving and loading ProcessMapPoint to/from JSON file."""
    # Create a process map point
    build_params = BuildParameters(
        beam_power=Quantity(250.0, "watt"),
        scan_velocity=Quantity(1.0, "meter / second"),
    )
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(110.0, "micrometer"),
        width=Quantity(85.0, "micrometer"),
        length=Quantity(160.0, "micrometer"),
        length_front=Quantity(65.0, "micrometer"),
        length_behind=Quantity(95.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=False,
        keyholing=True,
        balling=False,
    )

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    # Save to file
    path = tmp_path / "process_map_point.json"
    saved_path = point.save(path)
    assert saved_path.exists()

    # Load from file
    loaded_point = ProcessMapPoint.load(saved_path)

    # Verify build parameters
    assert (
        loaded_point.build_parameters.beam_power.magnitude
        == build_params.beam_power.magnitude
    )
    assert str(loaded_point.build_parameters.beam_power.units) == str(
        build_params.beam_power.units
    )
    assert (
        loaded_point.build_parameters.scan_velocity.magnitude
        == build_params.scan_velocity.magnitude
    )
    assert str(loaded_point.build_parameters.scan_velocity.units) == str(
        build_params.scan_velocity.units
    )

    # Verify melt pool dimensions
    assert (
        loaded_point.melt_pool_dimensions.depth.magnitude
        == melt_pool_dims.depth.magnitude
    )
    assert str(loaded_point.melt_pool_dimensions.depth.units) == str(
        melt_pool_dims.depth.units
    )
    assert (
        loaded_point.melt_pool_dimensions.width.magnitude
        == melt_pool_dims.width.magnitude
    )
    assert (
        loaded_point.melt_pool_dimensions.length.magnitude
        == melt_pool_dims.length.magnitude
    )

    # Verify classifications
    assert loaded_point.melt_pool_classifications.lack_of_fusion is False
    assert loaded_point.melt_pool_classifications.keyholing is True
    assert loaded_point.melt_pool_classifications.balling is False


def test_process_map_point_save_creates_directories(tmp_path: Path):
    """Test that save creates parent directories if they don't exist."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100.0, "micrometer"),
        width=Quantity(80.0, "micrometer"),
        length=Quantity(150.0, "micrometer"),
        length_front=Quantity(60.0, "micrometer"),
        length_behind=Quantity(90.0, "micrometer"),
    )
    classifications = MeltPoolClassifications()

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    # Save to nested path that doesn't exist
    nested_path = tmp_path / "nested" / "directory" / "point.json"
    saved_path = point.save(nested_path)

    assert saved_path.exists()
    assert saved_path.parent.exists()


def test_process_map_point_load_invalid_structure(tmp_path: Path):
    """Test that load raises ValueError for invalid JSON structure."""
    path = tmp_path / "invalid.json"
    # Write an array instead of a dict
    path.write_text('[{"key": "value"}]')

    with pytest.raises(ValueError, match="Unexpected JSON structure"):
        ProcessMapPoint.load(path)


def test_process_map_point_round_trip_with_all_fields(tmp_path: Path):
    """Test complete round-trip with all fields populated."""
    # Create point with custom values for all fields
    build_params = BuildParameters(
        beam_diameter=Quantity(6e-5, "meter"),
        beam_power=Quantity(275.0, "watt"),
        hatch_spacing=Quantity(55.0, "micrometer"),
        layer_height=Quantity(110.0, "micrometer"),
        scan_velocity=Quantity(1.1, "meter / second"),
        temperature_preheat=Quantity(350.0, "kelvin"),
    )
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(125.0, "micrometer"),
        width=Quantity(95.0, "micrometer"),
        length=Quantity(175.0, "micrometer"),
        length_front=Quantity(75.0, "micrometer"),
        length_behind=Quantity(100.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(
        lack_of_fusion=True,
        keyholing=True,
        balling=True,
    )

    original_point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    # Save and load
    path = tmp_path / "complete_point.json"
    original_point.save(path)
    loaded_point = ProcessMapPoint.load(path)

    # Verify all build parameters
    for field in [
        "beam_diameter",
        "beam_power",
        "hatch_spacing",
        "layer_height",
        "scan_velocity",
        "temperature_preheat",
    ]:
        original_q = getattr(original_point.build_parameters, field)
        loaded_q = getattr(loaded_point.build_parameters, field)
        assert loaded_q.magnitude == original_q.magnitude
        assert str(loaded_q.units) == str(original_q.units)

    # Verify all melt pool dimensions
    for field in ["depth", "width", "length", "length_front", "length_behind"]:
        original_q = getattr(original_point.melt_pool_dimensions, field)
        loaded_q = getattr(loaded_point.melt_pool_dimensions, field)
        assert loaded_q.magnitude == original_q.magnitude
        assert str(loaded_q.units) == str(original_q.units)

    # Verify all classifications
    assert (
        loaded_point.melt_pool_classifications.lack_of_fusion
        == original_point.melt_pool_classifications.lack_of_fusion
    )
    assert (
        loaded_point.melt_pool_classifications.keyholing
        == original_point.melt_pool_classifications.keyholing
    )
    assert (
        loaded_point.melt_pool_classifications.balling
        == original_point.melt_pool_classifications.balling
    )


# -------------------------------
# ProcessMapPoints tests
# -------------------------------


def test_process_map_points_empty_initialization():
    """Test creating ProcessMapPoints with empty list."""
    points_collection = ProcessMapPoints()
    assert points_collection.points == []
    assert len(points_collection.points) == 0


def test_process_map_points_with_single_point():
    """Test creating ProcessMapPoints with a single point."""
    build_params = BuildParameters()
    melt_pool_dims = MeltPoolDimensions(
        depth=Quantity(100.0, "micrometer"),
        width=Quantity(80.0, "micrometer"),
        length=Quantity(150.0, "micrometer"),
        length_front=Quantity(60.0, "micrometer"),
        length_behind=Quantity(90.0, "micrometer"),
    )
    classifications = MeltPoolClassifications(lack_of_fusion=False)

    point = ProcessMapPoint(
        build_parameters=build_params,
        melt_pool_dimensions=melt_pool_dims,
        melt_pool_classifications=classifications,
    )

    points_collection = ProcessMapPoints(points=[point])
    assert len(points_collection.points) == 1
    assert points_collection.points[0].melt_pool_classifications.lack_of_fusion is False


def test_process_map_points_with_multiple_points():
    """Test creating ProcessMapPoints with multiple points."""
    points = []
    for i in range(5):
        build_params = BuildParameters(
            beam_power=Quantity(200.0 + i * 50.0, "watt"),
            scan_velocity=Quantity(0.8 + i * 0.2, "meter / second"),
        )
        melt_pool_dims = MeltPoolDimensions(
            depth=Quantity(100.0 + i * 10.0, "micrometer"),
            width=Quantity(80.0 + i * 5.0, "micrometer"),
            length=Quantity(150.0 + i * 10.0, "micrometer"),
            length_front=Quantity(60.0 + i * 5.0, "micrometer"),
            length_behind=Quantity(90.0 + i * 5.0, "micrometer"),
        )
        classifications = MeltPoolClassifications(
            lack_of_fusion=i % 2 == 0,
            keyholing=i % 3 == 0,
            balling=False,
        )
        point = ProcessMapPoint(
            build_parameters=build_params,
            melt_pool_dimensions=melt_pool_dims,
            melt_pool_classifications=classifications,
        )
        points.append(point)

    points_collection = ProcessMapPoints(points=points)
    assert len(points_collection.points) == 5

    # Verify first point
    assert points_collection.points[0].build_parameters.beam_power.magnitude == 200.0
    assert points_collection.points[0].melt_pool_dimensions.depth.magnitude == 100.0

    # Verify last point
    assert points_collection.points[4].build_parameters.beam_power.magnitude == 400.0
    assert points_collection.points[4].melt_pool_dimensions.depth.magnitude == 140.0


def test_process_map_points_to_dict():
    """Test that ProcessMapPoints to_dict() properly serializes all points."""
    points = []
    for i in range(2):
        build_params = BuildParameters(
            beam_power=Quantity(250.0 + i * 50.0, "watt"),
        )
        melt_pool_dims = MeltPoolDimensions(
            depth=Quantity(110.0 + i * 10.0, "micrometer"),
            width=Quantity(85.0, "micrometer"),
            length=Quantity(160.0, "micrometer"),
            length_front=Quantity(65.0, "micrometer"),
            length_behind=Quantity(95.0, "micrometer"),
        )
        classifications = MeltPoolClassifications(lack_of_fusion=i == 1)
        point = ProcessMapPoint(
            build_parameters=build_params,
            melt_pool_dimensions=melt_pool_dims,
            melt_pool_classifications=classifications,
        )
        points.append(point)

    points_collection = ProcessMapPoints(points=points)
    data = points_collection.to_dict()

    assert "points" in data
    assert len(data["points"]) == 2

    # Verify first point serialization
    assert data["points"][0]["build_parameters"]["beam_power"]["magnitude"] == 250.0
    assert data["points"][0]["build_parameters"]["beam_power"]["units"] == "watt"
    assert data["points"][0]["melt_pool_classifications"]["lack_of_fusion"] is False

    # Verify second point serialization
    assert data["points"][1]["build_parameters"]["beam_power"]["magnitude"] == 300.0
    assert data["points"][1]["melt_pool_classifications"]["lack_of_fusion"] is True


def test_process_map_points_save_and_load(tmp_path: Path):
    """Test saving and loading ProcessMapPoints to/from JSON file."""
    # Create points collection
    points = []
    for i in range(3):
        build_params = BuildParameters(
            beam_power=Quantity(200.0 + i * 100.0, "watt"),
        )
        melt_pool_dims = MeltPoolDimensions(
            depth=Quantity(100.0 + i * 20.0, "micrometer"),
            width=Quantity(80.0, "micrometer"),
            length=Quantity(150.0, "micrometer"),
            length_front=Quantity(60.0, "micrometer"),
            length_behind=Quantity(90.0, "micrometer"),
        )
        classifications = MeltPoolClassifications(
            lack_of_fusion=i == 0,
            keyholing=i == 1,
            balling=i == 2,
        )
        point = ProcessMapPoint(
            build_parameters=build_params,
            melt_pool_dimensions=melt_pool_dims,
            melt_pool_classifications=classifications,
        )
        points.append(point)

    points_collection = ProcessMapPoints(points=points)

    # Save to file
    path = tmp_path / "process_map_points.json"
    saved_path = points_collection.save(path)
    assert saved_path.exists()

    # Load from file
    loaded_collection = ProcessMapPoints.load(saved_path)

    # Verify count
    assert len(loaded_collection.points) == 3

    # Verify each point
    for i in range(3):
        original = points_collection.points[i]
        loaded = loaded_collection.points[i]

        assert (
            loaded.build_parameters.beam_power.magnitude
            == original.build_parameters.beam_power.magnitude
        )
        assert (
            loaded.melt_pool_dimensions.depth.magnitude
            == original.melt_pool_dimensions.depth.magnitude
        )
        assert (
            loaded.melt_pool_classifications.lack_of_fusion
            == original.melt_pool_classifications.lack_of_fusion
        )
        assert (
            loaded.melt_pool_classifications.keyholing
            == original.melt_pool_classifications.keyholing
        )
        assert (
            loaded.melt_pool_classifications.balling
            == original.melt_pool_classifications.balling
        )


def test_process_map_points_save_empty_list(tmp_path: Path):
    """Test saving and loading empty ProcessMapPoints."""
    points_collection = ProcessMapPoints()

    path = tmp_path / "empty_points.json"
    points_collection.save(path)

    loaded_collection = ProcessMapPoints.load(path)
    assert len(loaded_collection.points) == 0
    assert loaded_collection.points == []


def test_process_map_points_save_creates_directories(tmp_path: Path):
    """Test that save creates parent directories if they don't exist."""
    points_collection = ProcessMapPoints()

    nested_path = tmp_path / "nested" / "directories" / "points.json"
    saved_path = points_collection.save(nested_path)

    assert saved_path.exists()
    assert saved_path.parent.exists()


def test_process_map_points_load_invalid_structure(tmp_path: Path):
    """Test that load raises ValueError for invalid JSON structure."""
    path = tmp_path / "invalid.json"
    # Write an array instead of a dict
    path.write_text('[{"points": []}]')

    with pytest.raises(ValueError, match="Unexpected JSON structure"):
        ProcessMapPoints.load(path)


def test_process_map_points_round_trip_with_varied_data(tmp_path: Path):
    """Test complete round-trip with varied data in points."""
    points = []

    # Point 1: Default parameters, no defects
    points.append(
        ProcessMapPoint(
            build_parameters=BuildParameters(),
            melt_pool_dimensions=MeltPoolDimensions(
                depth=Quantity(100.0, "micrometer"),
                width=Quantity(80.0, "micrometer"),
                length=Quantity(150.0, "micrometer"),
                length_front=Quantity(60.0, "micrometer"),
                length_behind=Quantity(90.0, "micrometer"),
            ),
            melt_pool_classifications=MeltPoolClassifications(
                lack_of_fusion=False,
                keyholing=False,
                balling=False,
            ),
        )
    )

    # Point 2: Custom parameters, with defects
    points.append(
        ProcessMapPoint(
            build_parameters=BuildParameters(
                beam_power=Quantity(350.0, "watt"),
                scan_velocity=Quantity(1.5, "meter / second"),
            ),
            melt_pool_dimensions=MeltPoolDimensions(
                depth=Quantity(150.0, "micrometer"),
                width=Quantity(120.0, "micrometer"),
                length=Quantity(200.0, "micrometer"),
                length_front=Quantity(80.0, "micrometer"),
                length_behind=Quantity(120.0, "micrometer"),
            ),
            melt_pool_classifications=MeltPoolClassifications(
                lack_of_fusion=True,
                keyholing=True,
                balling=False,
            ),
        )
    )

    # Point 3: Mixed classifications
    points.append(
        ProcessMapPoint(
            build_parameters=BuildParameters(
                beam_power=Quantity(180.0, "watt"),
            ),
            melt_pool_dimensions=MeltPoolDimensions(
                depth=Quantity(80.0, "micrometer"),
                width=Quantity(60.0, "micrometer"),
                length=Quantity(120.0, "micrometer"),
                length_front=Quantity(50.0, "micrometer"),
                length_behind=Quantity(70.0, "micrometer"),
            ),
            melt_pool_classifications=MeltPoolClassifications(
                lack_of_fusion=None,
                keyholing=False,
                balling=True,
            ),
        )
    )

    original_collection = ProcessMapPoints(points=points)

    # Save and load
    path = tmp_path / "varied_points.json"
    original_collection.save(path)
    loaded_collection = ProcessMapPoints.load(path)

    # Verify all points
    assert len(loaded_collection.points) == 3

    # Verify point 1
    assert (
        loaded_collection.points[0].build_parameters.beam_power.magnitude == 200.0
    )  # default
    assert loaded_collection.points[0].melt_pool_classifications.lack_of_fusion is False

    # Verify point 2
    assert loaded_collection.points[1].build_parameters.beam_power.magnitude == 350.0
    assert loaded_collection.points[1].build_parameters.scan_velocity.magnitude == 1.5
    assert loaded_collection.points[1].melt_pool_classifications.lack_of_fusion is True
    assert loaded_collection.points[1].melt_pool_classifications.keyholing is True

    # Verify point 3
    assert loaded_collection.points[2].build_parameters.beam_power.magnitude == 180.0
    assert loaded_collection.points[2].melt_pool_classifications.lack_of_fusion is None
    assert loaded_collection.points[2].melt_pool_classifications.balling is True
