import pytest
import numpy as np
import matplotlib

matplotlib.use("Agg")

from pathlib import Path
from shapely.geometry import Polygon, LineString, MultiLineString
from shapely import wkb, wkt
from unittest.mock import Mock

from am.slicer.utils.infill import infill_rectilinear, infill_visualization


class MockSection:
    """Mock section object for testing."""

    def __init__(self, polygons):
        self.polygons_full = polygons


# -------------------------------
# infill_rectilinear tests
# -------------------------------


def test_infill_rectilinear_none_section(tmp_path):
    """Test that None section returns None."""
    result = infill_rectilinear(
        section=None,
        horizontal=True,
        hatch_spacing=0.05,
        data_out_path=tmp_path,
        index_string="test",
        binary=True,
    )
    assert result is None


def test_infill_rectilinear_horizontal_binary(tmp_path):
    """Test horizontal infill generation with binary output."""
    # Create a simple square polygon
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=0.2,
        data_out_path=tmp_path,
        index_string="layer_001",
        binary=True,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".wkb"
    assert result.name == "layer_001.wkb"

    # Verify file contents can be read back
    with open(result, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        # Check that lines are hex-encoded
        for line in lines:
            line = line.strip()
            if line:
                bytes.fromhex(line)  # Should not raise


def test_infill_rectilinear_horizontal_text(tmp_path):
    """Test horizontal infill generation with text output."""
    polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="layer_002",
        binary=False,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".txt"
    assert result.name == "layer_002.txt"

    # Verify file contents are WKT format
    with open(result, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        for line in lines:
            line = line.strip()
            if line:
                geom = wkt.loads(line)
                assert geom is not None


def test_infill_rectilinear_vertical_binary(tmp_path):
    """Test vertical infill generation with binary output."""
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=False,
        hatch_spacing=0.25,
        data_out_path=tmp_path,
        index_string="layer_003",
        binary=True,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".wkb"

    # Read back and verify geometries
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) > 0

        for line in lines:
            g_bytes = bytes.fromhex(line)
            geom = wkb.loads(g_bytes)
            assert geom is not None


def test_infill_rectilinear_vertical_text(tmp_path):
    """Test vertical infill generation with text output."""
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=False,
        hatch_spacing=0.3,
        data_out_path=tmp_path,
        index_string="layer_004",
        binary=False,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".txt"


def test_infill_rectilinear_multiple_polygons(tmp_path):
    """Test infill generation with multiple polygons."""
    polygon1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    polygon2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
    section = MockSection([polygon1, polygon2])

    result = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=0.2,
        data_out_path=tmp_path,
        index_string="layer_005",
        binary=True,
    )

    assert result is not None
    assert result.exists()

    # Should have intersections from both polygons
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        # Should have multiple intersection lines
        assert len(lines) > 0


def test_infill_rectilinear_complex_polygon(tmp_path):
    """Test infill with polygon that has holes."""
    # Outer boundary
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    # Inner hole
    inner = [(2, 2), (8, 2), (8, 8), (2, 8)]
    polygon = Polygon(outer, [inner])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=1.0,
        data_out_path=tmp_path,
        index_string="layer_006",
        binary=False,
    )

    assert result is not None
    assert result.exists()


def test_infill_rectilinear_small_hatch_spacing(tmp_path):
    """Test with very small hatch spacing."""
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    section = MockSection([polygon])

    result = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=0.05,  # Small spacing = many lines
        data_out_path=tmp_path,
        index_string="layer_007",
        binary=True,
    )

    assert result is not None
    assert result.exists()

    # Verify many intersection lines
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) > 10


# -------------------------------
# infill_visualization tests
# -------------------------------


def test_infill_visualization_binary(tmp_path):
    """Test visualization with binary WKB input."""
    # Create test infill file
    polygon = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    section = MockSection([polygon])

    infill_file = infill_rectilinear(
        section=section,
        horizontal=True,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_001",
        binary=True,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    result = infill_visualization(
        infill_file=infill_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        infill_images_out_path=images_path,
    )

    assert result == infill_file.name

    # Check that image was created
    image_file = images_path / "vis_001.png"
    assert image_file.exists()


def test_infill_visualization_text(tmp_path):
    """Test visualization with text WKT input."""
    polygon = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    section = MockSection([polygon])

    infill_file = infill_rectilinear(
        section=section,
        horizontal=False,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_002",
        binary=False,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    result = infill_visualization(
        infill_file=infill_file,
        binary=False,
        mesh_bounds=mesh_bounds,
        infill_images_out_path=images_path,
    )

    assert result == infill_file.name

    image_file = images_path / "vis_002.png"
    assert image_file.exists()


def test_infill_visualization_empty_geometry(tmp_path):
    """Test visualization handles empty geometries."""
    # Create file with empty geometry
    infill_file = tmp_path / "empty.wkb"
    empty_line = LineString()
    with open(infill_file, "w") as f:
        f.write(wkb.dumps(empty_line).hex())

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    # Should handle empty geometry gracefully
    result = infill_visualization(
        infill_file=infill_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        infill_images_out_path=images_path,
    )

    # Function returns None for empty geometries
    assert result is None


def test_infill_visualization_multilinestring(tmp_path):
    """Test visualization with MultiLineString geometries."""
    # Create file with MultiLineString
    infill_file = tmp_path / "multi.wkb"
    line1 = LineString([(0, 0), (1, 1)])
    line2 = LineString([(1, 0), (2, 1)])
    multi = MultiLineString([line1, line2])

    with open(infill_file, "w") as f:
        f.write(wkb.dumps(multi).hex())

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [2, 2]])

    result = infill_visualization(
        infill_file=infill_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        infill_images_out_path=images_path,
    )

    assert result == infill_file.name
    image_file = images_path / "multi.png"
    assert image_file.exists()


def test_infill_visualization_malformed_geometry(tmp_path):
    """Test that malformed geometries are handled gracefully."""
    # Create file with malformed data
    infill_file = tmp_path / "malformed.wkb"
    with open(infill_file, "w") as f:
        f.write("notvalidhex\n")
        f.write("alsoinvalid\n")

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    # Should not raise, just skip malformed geometries
    result = infill_visualization(
        infill_file=infill_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        infill_images_out_path=images_path,
    )

    # Should still create output (even if empty)
    image_file = images_path / "malformed.png"
    assert image_file.exists()
