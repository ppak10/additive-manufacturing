import pytest
import numpy as np
import matplotlib

matplotlib.use("Agg")

from pathlib import Path
from shapely.geometry import Polygon, LineString, MultiLineString
from shapely import wkb, wkt

from am.slicer.utils.contour import contour_generate
from am.slicer.utils.visualize_2d import toolpath_visualization as contour_visualization


class MockSection:
    """Mock section object for testing."""

    def __init__(self, polygons):
        self.polygons_full = polygons


# -------------------------------
# contour_generate tests
# -------------------------------


def test_contour_generate_none_section(tmp_path):
    """Test that None section returns None."""
    result = contour_generate(
        section=None,
        hatch_spacing=0.05,
        data_out_path=tmp_path,
        index_string="test",
        binary=True,
    )
    assert result is None


def test_contour_generate_simple_polygon_binary(tmp_path):
    """Test contour generation with simple polygon in binary format."""
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.05,
        data_out_path=tmp_path,
        index_string="contour_001",
        binary=True,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".wkb"
    assert result.name == "contour_001.wkb"

    # Verify file contents can be read back
    with open(result, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        # Should have at least one perimeter (exterior)
        for line in lines:
            line = line.strip()
            if line:
                g_bytes = bytes.fromhex(line)
                geom = wkb.loads(g_bytes)
                assert isinstance(geom, LineString)


def test_contour_generate_simple_polygon_text(tmp_path):
    """Test contour generation with simple polygon in text format."""
    polygon = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.1,
        data_out_path=tmp_path,
        index_string="contour_002",
        binary=False,
    )

    assert result is not None
    assert result.exists()
    assert result.suffix == ".txt"
    assert result.name == "contour_002.txt"

    # Verify file contents are WKT format
    with open(result, "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        for line in lines:
            line = line.strip()
            if line:
                geom = wkt.loads(line)
                assert isinstance(geom, LineString)


def test_contour_generate_polygon_with_hole(tmp_path):
    """Test contour generation with polygon containing holes."""
    # Outer boundary
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    # Inner hole
    inner = [(2, 2), (8, 2), (8, 8), (2, 8)]
    polygon = Polygon(outer, [inner])
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="contour_003",
        binary=True,
    )

    assert result is not None
    assert result.exists()

    # Should have both exterior and interior perimeters
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        # One exterior + one interior = 2 perimeters
        assert len(lines) == 2


def test_contour_generate_polygon_with_multiple_holes(tmp_path):
    """Test contour generation with multiple holes."""
    outer = [(0, 0), (20, 0), (20, 20), (0, 20)]
    hole1 = [(2, 2), (5, 2), (5, 5), (2, 5)]
    hole2 = [(7, 7), (10, 7), (10, 10), (7, 10)]
    hole3 = [(12, 12), (15, 12), (15, 15), (12, 15)]
    polygon = Polygon(outer, [hole1, hole2, hole3])
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="contour_004",
        binary=False,
    )

    assert result is not None
    assert result.exists()

    # Should have exterior + 3 interior perimeters
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 4  # 1 exterior + 3 interiors


def test_contour_generate_multiple_polygons(tmp_path):
    """Test contour generation with multiple separate polygons."""
    polygon1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    polygon2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3)])
    polygon3 = Polygon([(4, 4), (5, 4), (5, 5), (4, 5)])
    section = MockSection([polygon1, polygon2, polygon3])

    result = contour_generate(
        section=section,
        hatch_spacing=0.1,
        data_out_path=tmp_path,
        index_string="contour_005",
        binary=True,
    )

    assert result is not None
    assert result.exists()

    # Should have 3 perimeters (one per polygon)
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 3


def test_contour_generate_complex_section(tmp_path):
    """Test contour generation with complex section having multiple polygons with holes."""
    # First polygon with hole
    outer1 = [(0, 0), (5, 0), (5, 5), (0, 5)]
    inner1 = [(1, 1), (4, 1), (4, 4), (1, 4)]
    polygon1 = Polygon(outer1, [inner1])

    # Second polygon without hole
    polygon2 = Polygon([(6, 6), (10, 6), (10, 10), (6, 10)])

    section = MockSection([polygon1, polygon2])

    result = contour_generate(
        section=section,
        hatch_spacing=0.2,
        data_out_path=tmp_path,
        index_string="contour_006",
        binary=True,
    )

    assert result is not None
    assert result.exists()

    # Should have 3 perimeters: 2 from polygon1 (exterior + interior), 1 from polygon2
    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 3


def test_contour_generate_triangle(tmp_path):
    """Test contour generation with triangular polygon."""
    polygon = Polygon([(0, 0), (1, 0), (0.5, 1)])
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.05,
        data_out_path=tmp_path,
        index_string="contour_007",
        binary=False,
    )

    assert result is not None
    assert result.exists()

    with open(result, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
        assert len(lines) == 1


def test_contour_generate_coordinates_preserved(tmp_path):
    """Test that exterior coordinates are properly preserved."""
    coords = [(0, 0), (3, 0), (3, 4), (0, 4)]
    polygon = Polygon(coords)
    section = MockSection([polygon])

    result = contour_generate(
        section=section,
        hatch_spacing=0.1,
        data_out_path=tmp_path,
        index_string="contour_008",
        binary=False,
    )

    assert result is not None

    # Read back and verify coordinates
    with open(result, "r") as f:
        line = f.readline().strip()
        geom = wkt.loads(line)
        result_coords = list(geom.coords)

        # First and last should be the same (closed ring)
        assert result_coords[0] == result_coords[-1]
        # Should have 5 coordinates (4 vertices + closing point)
        assert len(result_coords) == 5


# -------------------------------
# contour_visualization tests
# -------------------------------


def test_contour_visualization_binary(tmp_path):
    """Test visualization with binary WKB input."""
    polygon = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    section = MockSection([polygon])

    contour_file = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_001",
        binary=True,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    result = contour_visualization(
        toolpath_file=contour_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    assert result == contour_file.name

    # Check that image was created
    image_file = images_path / "vis_001.png"
    assert image_file.exists()


def test_contour_visualization_text(tmp_path):
    """Test visualization with text WKT input."""
    polygon = Polygon([(0, 0), (5, 0), (5, 5), (0, 5)])
    section = MockSection([polygon])

    contour_file = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_002",
        binary=False,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    result = contour_visualization(
        toolpath_file=contour_file,
        binary=False,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    assert result == contour_file.name

    image_file = images_path / "vis_002.png"
    assert image_file.exists()


def test_contour_visualization_with_hole(tmp_path):
    """Test visualization with polygon containing holes."""
    outer = [(0, 0), (10, 0), (10, 10), (0, 10)]
    inner = [(2, 2), (8, 2), (8, 8), (2, 8)]
    polygon = Polygon(outer, [inner])
    section = MockSection([polygon])

    contour_file = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_003",
        binary=True,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [10, 10]])

    result = contour_visualization(
        toolpath_file=contour_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    assert result == contour_file.name

    image_file = images_path / "vis_003.png"
    assert image_file.exists()


def test_contour_visualization_empty_geometry(tmp_path):
    """Test visualization handles empty geometries."""
    contour_file = tmp_path / "empty.wkb"
    empty_line = LineString()
    with open(contour_file, "w") as f:
        f.write(wkb.dumps(empty_line).hex())

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    # Should handle empty geometry gracefully
    result = contour_visualization(
        toolpath_file=contour_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    # Function still creates output even with empty geometries
    assert result == contour_file.name
    image_file = images_path / "empty.png"
    assert image_file.exists()


def test_contour_visualization_multilinestring(tmp_path):
    """Test visualization with MultiLineString geometries."""
    contour_file = tmp_path / "multi.wkb"
    line1 = LineString([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    line2 = LineString([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)])
    multi = MultiLineString([line1, line2])

    with open(contour_file, "w") as f:
        f.write(wkb.dumps(multi).hex())

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [3, 3]])

    result = contour_visualization(
        toolpath_file=contour_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    assert result == contour_file.name
    image_file = images_path / "multi.png"
    assert image_file.exists()


def test_contour_visualization_malformed_geometry(tmp_path):
    """Test that malformed geometries are handled gracefully."""
    contour_file = tmp_path / "malformed.wkb"
    with open(contour_file, "w") as f:
        f.write("notvalidhex\n")
        f.write("alsoinvalid\n")

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    # Should not raise, just skip malformed geometries
    result = contour_visualization(
        toolpath_file=contour_file,
        binary=True,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    # Should still create output (even if empty)
    image_file = images_path / "malformed.png"
    assert image_file.exists()


def test_contour_visualization_multiple_perimeters(tmp_path):
    """Test visualization with multiple perimeters."""
    polygon1 = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
    polygon2 = Polygon([(3, 3), (5, 3), (5, 5), (3, 5)])
    section = MockSection([polygon1, polygon2])

    contour_file = contour_generate(
        section=section,
        hatch_spacing=0.5,
        data_out_path=tmp_path,
        index_string="vis_004",
        binary=False,
    )

    images_path = tmp_path / "images"
    images_path.mkdir()

    mesh_bounds = np.array([[0, 0], [5, 5]])

    result = contour_visualization(
        toolpath_file=contour_file,
        binary=False,
        mesh_bounds=mesh_bounds,
        images_out_path=images_path,
    )

    assert result == contour_file.name
    image_file = images_path / "vis_004.png"
    assert image_file.exists()
