import pytest
from am.process_map.classification import (
    KEYHOLE_THRESHOLD,
    BALLING_THRESHOLD,
    keyhole,
    lack_of_fusion,
    balling,
)


# -------------------------------
# Keyhole tests
# -------------------------------


def test_keyhole_exactly_at_threshold():
    """Test keyhole at exactly the threshold value (edge case)."""
    width = KEYHOLE_THRESHOLD
    depth = 1.0
    assert keyhole(width, depth) is True


def test_keyhole_below_threshold():
    """Test keyhole when width/depth is below threshold (keyholing detected)."""
    width = 1.0
    depth = 1.0
    # width/depth = 1.0, which is below 1.5
    assert keyhole(width, depth) is True


def test_keyhole_above_threshold():
    """Test keyhole when width/depth is above threshold (no keyholing)."""
    width = 2.0
    depth = 1.0
    # width/depth = 2.0, which is above 1.5
    assert keyhole(width, depth) is False


def test_keyhole_very_narrow():
    """Test keyhole with very narrow width (strong keyholing)."""
    width = 0.5
    depth = 1.0
    # width/depth = 0.5, very narrow
    assert keyhole(width, depth) is True


def test_keyhole_very_wide():
    """Test keyhole with very wide width (no keyholing)."""
    width = 10.0
    depth = 1.0
    # width/depth = 10.0, very wide
    assert keyhole(width, depth) is False


def test_keyhole_with_decimal_values():
    """Test keyhole with realistic decimal values."""
    width = 80.0  # micrometers
    depth = 100.0  # micrometers
    # width/depth = 0.8
    assert keyhole(width, depth) is True


def test_keyhole_equal_width_depth():
    """Test keyhole when width equals depth."""
    width = 1.0
    depth = 1.0
    # width/depth = 1.0, below threshold
    assert keyhole(width, depth) is True


# -------------------------------
# Lack of fusion tests
# -------------------------------


def test_lack_of_fusion_exactly_at_threshold():
    """Test lack of fusion at exactly the threshold (edge case)."""
    # (hatch/width)^2 + (layer/depth)^2 = 1
    hatch_spacing = 0.8
    layer_height = 0.6
    width = 0.8
    depth = 0.6
    # (0.8/0.8)^2 + (0.6/0.6)^2 = 1 + 1 = 2 > 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is True


def test_lack_of_fusion_above_threshold():
    """Test lack of fusion when value is above threshold (defect detected)."""
    hatch_spacing = 100.0
    layer_height = 100.0
    width = 50.0
    depth = 50.0
    # (100/50)^2 + (100/50)^2 = 4 + 4 = 8 > 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is True


def test_lack_of_fusion_below_threshold():
    """Test lack of fusion when value is below threshold (no defect)."""
    hatch_spacing = 30.0
    layer_height = 30.0
    width = 100.0
    depth = 100.0
    # (30/100)^2 + (30/100)^2 = 0.09 + 0.09 = 0.18 < 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is False


def test_lack_of_fusion_small_spacing_large_pool():
    """Test lack of fusion with small spacing and large melt pool (good conditions)."""
    hatch_spacing = 20.0
    layer_height = 20.0
    width = 150.0
    depth = 150.0
    # (20/150)^2 + (20/150)^2 ≈ 0.018 + 0.018 = 0.036 < 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is False


def test_lack_of_fusion_large_spacing_small_pool():
    """Test lack of fusion with large spacing and small melt pool (bad conditions)."""
    hatch_spacing = 150.0
    layer_height = 150.0
    width = 50.0
    depth = 50.0
    # (150/50)^2 + (150/50)^2 = 9 + 9 = 18 > 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is True


def test_lack_of_fusion_realistic_values():
    """Test lack of fusion with realistic manufacturing values."""
    hatch_spacing = 50.0  # micrometers
    layer_height = 100.0  # micrometers
    width = 80.0  # micrometers
    depth = 100.0  # micrometers
    # (50/80)^2 + (100/100)^2 = 0.390625 + 1 = 1.390625 > 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is True


def test_lack_of_fusion_good_overlap():
    """Test lack of fusion with good overlap (no defect expected)."""
    hatch_spacing = 40.0
    layer_height = 50.0
    width = 100.0
    depth = 120.0
    # (40/100)^2 + (50/120)^2 = 0.16 + 0.1736 = 0.3336 < 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is False


def test_lack_of_fusion_asymmetric_conditions():
    """Test lack of fusion with asymmetric hatch and layer conditions."""
    hatch_spacing = 90.0
    layer_height = 40.0
    width = 100.0
    depth = 100.0
    # (90/100)^2 + (40/100)^2 = 0.81 + 0.16 = 0.97 < 1
    assert lack_of_fusion(hatch_spacing, layer_height, width, depth) is False


# -------------------------------
# Balling tests
# -------------------------------


def test_balling_exactly_at_threshold():
    """Test balling at exactly the threshold value (edge case)."""
    length = BALLING_THRESHOLD
    width = 1.0
    # length/width = 2.0, exactly at threshold
    assert balling(length, width) is False


def test_balling_above_threshold():
    """Test balling when length/width is above threshold (defect detected)."""
    length = 250.0
    width = 100.0
    # length/width = 2.5 > 2.0
    assert balling(length, width) is True


def test_balling_below_threshold():
    """Test balling when length/width is below threshold (no defect)."""
    length = 150.0
    width = 100.0
    # length/width = 1.5 < 2.0
    assert balling(length, width) is False


def test_balling_very_elongated():
    """Test balling with very elongated melt pool (strong balling)."""
    length = 500.0
    width = 100.0
    # length/width = 5.0 > 2.0
    assert balling(length, width) is True


def test_balling_nearly_circular():
    """Test balling with nearly circular melt pool (no balling)."""
    length = 100.0
    width = 100.0
    # length/width = 1.0 < 2.0
    assert balling(length, width) is False


def test_balling_realistic_values():
    """Test balling with realistic manufacturing values."""
    length = 150.0  # micrometers
    width = 80.0  # micrometers
    # length/width = 1.875 < 2.0
    assert balling(length, width) is False


def test_balling_slightly_above_threshold():
    """Test balling just above threshold."""
    length = 201.0
    width = 100.0
    # length/width = 2.01 > 2.0
    assert balling(length, width) is True


def test_balling_slightly_below_threshold():
    """Test balling just below threshold."""
    length = 199.0
    width = 100.0
    # length/width = 1.99 < 2.0
    assert balling(length, width) is False


# -------------------------------
# Edge case and error handling tests
# -------------------------------


def test_keyhole_with_zero_depth():
    """Test keyhole with zero depth (should raise error or return inf)."""
    width = 100.0
    depth = 0.0
    with pytest.raises(ZeroDivisionError):
        keyhole(width, depth)


def test_lack_of_fusion_with_zero_width():
    """Test lack of fusion with zero width (should raise error or return inf)."""
    hatch_spacing = 50.0
    layer_height = 100.0
    width = 0.0
    depth = 100.0
    with pytest.raises(ZeroDivisionError):
        lack_of_fusion(hatch_spacing, layer_height, width, depth)


def test_lack_of_fusion_with_zero_depth():
    """Test lack of fusion with zero depth (should raise error or return inf)."""
    hatch_spacing = 50.0
    layer_height = 100.0
    width = 100.0
    depth = 0.0
    with pytest.raises(ZeroDivisionError):
        lack_of_fusion(hatch_spacing, layer_height, width, depth)


def test_balling_with_zero_width():
    """Test balling with zero width (should raise error or return inf)."""
    length = 150.0
    width = 0.0
    with pytest.raises(ZeroDivisionError):
        balling(length, width)


# -------------------------------
# Integration-style tests
# -------------------------------


def test_all_functions_with_same_dimensions():
    """Test all functions with the same set of dimensions."""
    width = 100.0
    depth = 150.0
    length = 200.0
    hatch_spacing = 50.0
    layer_height = 100.0

    # Test keyhole
    keyhole_result = keyhole(width, depth)
    assert keyhole_result is True  # 100/150 = 0.67 < 1.5

    # Test lack of fusion
    lof_result = lack_of_fusion(hatch_spacing, layer_height, width, depth)
    assert lof_result is False  # (50/100)^2 + (100/150)^2 = 0.25 + 0.44 = 0.69 < 1

    # Test balling
    balling_result = balling(length, width)
    assert balling_result is False  # 200/100 = 2.0, at threshold


def test_good_process_parameters():
    """Test with parameters expected to produce good results (no defects)."""
    width = 120.0
    depth = 80.0
    length = 180.0
    hatch_spacing = 60.0
    layer_height = 60.0

    assert keyhole(width, depth) is True  # 120/80 = 1.5, at threshold (<=)
    assert (
        lack_of_fusion(hatch_spacing, layer_height, width, depth) is False
    )  # (60/120)^2 + (60/80)^2 = 0.25 + 0.5625 = 0.8125 < 1
    assert balling(length, width) is False  # 180/120 = 1.5 < 2.0


def test_poor_process_parameters():
    """Test with parameters expected to produce defects."""
    width = 50.0
    depth = 100.0
    length = 300.0
    hatch_spacing = 100.0
    layer_height = 150.0

    assert keyhole(width, depth) is True  # 50/100 = 0.5 < 1.5
    assert (
        lack_of_fusion(hatch_spacing, layer_height, width, depth) is True
    )  # (100/50)^2 + (150/100)^2 = 4 + 2.25 = 6.25 > 1
    assert balling(length, width) is True  # 300/50 = 6.0 > 2.0
