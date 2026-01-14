import pytest
from pint import Quantity

from am.simulator.tool.process_map.utils.parameter_ranges import (
    parse_shorthand,
    parse_options,
    inputs_to_parameter_ranges,
)
from am.simulator.tool.process_map.models.process_map_parameter_range import (
    ProcessMapParameterRange,
)


class TestParseShorthand:
    """Test the parse_shorthand function."""

    def test_parse_name_only(self):
        """Test parsing parameter with name only (uses defaults)."""
        result = parse_shorthand(["beam_power"])

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 1000
        assert result.step.magnitude == 100
        assert result.units == "watt"

    def test_parse_with_start_stop(self):
        """Test parsing parameter with start and stop values."""
        result = parse_shorthand(["beam_power", "150", "900"])

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 150
        assert result.stop.magnitude == 900
        assert result.step.magnitude == 100  # Default step

    def test_parse_with_full_range(self):
        """Test parsing parameter with start, stop, and step."""
        result = parse_shorthand(["beam_power", "100", "1000", "50"])

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 1000
        assert result.step.magnitude == 50

    def test_parse_with_full_range_and_units(self):
        """Test parsing parameter with full range and units."""
        result = parse_shorthand(["beam_power", "100", "1000", "50", "watts"])

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 1000
        assert result.step.magnitude == 50
        assert result.units == "watt"

    def test_parse_scan_velocity(self):
        """Test parsing scan_velocity parameter."""
        result = parse_shorthand(["scan_velocity", "100", "2000", "100"])

        assert result is not None
        assert result.name == "scan_velocity"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 2000
        assert result.step.magnitude == 100

    def test_parse_layer_height(self):
        """Test parsing layer_height parameter."""
        result = parse_shorthand(["layer_height"])

        assert result is not None
        assert result.name == "layer_height"
        assert result.start.magnitude == 25
        assert result.stop.magnitude == 100
        assert result.step.magnitude == 25
        assert result.units == "micron"

    def test_parse_empty_list_returns_none(self):
        """Test that empty list returns None."""
        result = parse_shorthand([])
        assert result is None

    def test_parse_none_returns_none(self):
        """Test that None returns None."""
        result = parse_shorthand(None)
        assert result is None

    def test_parse_invalid_parameter_name_raises_error(self):
        """Test that invalid parameter name raises exception."""
        with pytest.raises(Exception) as exc_info:
            parse_shorthand(["invalid_param"])

        assert "parameter name: invalid_param is invalid" in str(exc_info.value)

    def test_parse_with_different_units(self):
        """Test parsing with explicit different units."""
        result = parse_shorthand(
            ["scan_velocity", "100", "2000", "100", "millimeter / second"]
        )

        assert result is not None
        assert result.name == "scan_velocity"
        assert result.units == "millimeter / second"


class TestParseOptions:
    """Test the parse_options function."""

    def test_parse_shorthand_only(self):
        """Test parsing with shorthand only."""
        result = parse_options(
            shorthand=["beam_power", "100", "1000", "50"],
            name=None,
            range_values=None,
            units=None,
        )

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 1000
        assert result.step.magnitude == 50

    def test_parse_name_only(self):
        """Test parsing with name only (uses defaults)."""
        result = parse_options(
            shorthand=None,
            name="beam_power",
            range_values=None,
            units=None,
        )

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 100
        assert result.stop.magnitude == 1000
        assert result.step.magnitude == 100

    def test_parse_name_and_range(self):
        """Test parsing with name and range values."""
        result = parse_options(
            shorthand=None,
            name="beam_power",
            range_values=[150, 900, 50],
            units=None,
        )

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 150
        assert result.stop.magnitude == 900
        assert result.step.magnitude == 50

    def test_parse_name_range_and_units(self):
        """Test parsing with name, range, and units."""
        result = parse_options(
            shorthand=None,
            name="beam_power",
            range_values=[200, 800, 50],
            units="watts",
        )

        assert result is not None
        assert result.name == "beam_power"
        assert result.start.magnitude == 200
        assert result.stop.magnitude == 800
        assert result.step.magnitude == 50
        assert result.units == "watt"

    def test_verbose_overrides_shorthand_name(self):
        """Test that verbose name overrides shorthand name."""
        result = parse_options(
            shorthand=["scan_velocity"],
            name="beam_power",
            range_values=None,
            units=None,
        )

        assert result is not None
        assert result.name == "beam_power"

    def test_verbose_range_overrides_shorthand_range(self):
        """Test that verbose range overrides shorthand range."""
        result = parse_options(
            shorthand=["beam_power", "100", "1000", "100"],
            name=None,
            range_values=[200, 800, 50],
            units=None,
        )

        assert result is not None
        assert result.start.magnitude == 200
        assert result.stop.magnitude == 800
        assert result.step.magnitude == 50

    def test_range_with_two_values_only(self):
        """Test that range with two values sets start and stop only."""
        result = parse_options(
            shorthand=None,
            name="beam_power",
            range_values=[150, 900],
            units=None,
        )

        assert result is not None
        assert result.start.magnitude == 150
        assert result.stop.magnitude == 900
        assert result.step.magnitude == 100  # Uses default

    def test_invalid_name_returns_none(self):
        """Test that invalid name returns None."""
        result = parse_options(
            shorthand=None,
            name="invalid_param",
            range_values=None,
            units=None,
        )

        assert result is None

    def test_no_inputs_returns_none(self):
        """Test that no inputs returns None."""
        result = parse_options(
            shorthand=None,
            name=None,
            range_values=None,
            units=None,
        )

        assert result is None


class TestInputsToParameterRanges:
    """Test the inputs_to_parameter_ranges function."""

    def test_no_inputs_uses_defaults(self):
        """Test that no inputs creates default parameters."""
        result = inputs_to_parameter_ranges(
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert len(result) == 3
        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"
        assert result[2].name == "layer_height"

    def test_single_parameter_shorthand(self):
        """Test creating single parameter with shorthand."""
        result = inputs_to_parameter_ranges(
            (["beam_power", "100", "1000", "50"], None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert len(result) == 1
        assert result[0].name == "beam_power"
        assert result[0].start.magnitude == 100
        assert result[0].stop.magnitude == 1000
        assert result[0].step.magnitude == 50

    def test_single_parameter_verbose(self):
        """Test creating single parameter with verbose options."""
        result = inputs_to_parameter_ranges(
            (None, "beam_power", [150, 900, 50], "watts"),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert len(result) == 1
        assert result[0].name == "beam_power"
        assert result[0].start.magnitude == 150
        assert result[0].stop.magnitude == 900
        assert result[0].step.magnitude == 50

    def test_single_parameter_name_only(self):
        """Test creating single parameter with name only."""
        result = inputs_to_parameter_ranges(
            (None, "beam_power", None, None),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert len(result) == 1
        assert result[0].name == "beam_power"
        # Should use defaults
        assert result[0].start.magnitude == 100
        assert result[0].stop.magnitude == 1000

    def test_multiple_parameters(self):
        """Test creating multiple parameters."""
        result = inputs_to_parameter_ranges(
            (["beam_power"], None, None, None),
            (["scan_velocity", "100", "2000", "100"], None, None, None),
            (None, "layer_height", None, None),
        )

        assert len(result) == 3
        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"
        assert result[1].start.magnitude == 100
        assert result[2].name == "layer_height"

    def test_two_parameters_only(self):
        """Test creating only two parameters."""
        result = inputs_to_parameter_ranges(
            (["beam_power", "100", "1000", "50"], None, None, None),
            (["scan_velocity"], None, None, None),
            (None, None, None, None),
        )

        assert len(result) == 2
        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"

    def test_mixed_shorthand_and_verbose(self):
        """Test mixing shorthand and verbose options."""
        result = inputs_to_parameter_ranges(
            (["beam_power"], None, None, None),
            (None, "scan_velocity", [100, 2000, 100], None),
            (["layer_height", "25", "100", "25"], None, None, None),
        )

        assert len(result) == 3
        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"
        assert result[1].start.magnitude == 100
        assert result[2].name == "layer_height"

    def test_empty_tuples_returns_defaults(self):
        """Test that empty tuples return default parameters."""
        result = inputs_to_parameter_ranges(
            (None, None, None, None),
        )

        assert len(result) == 3
        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"
        assert result[2].name == "layer_height"

    def test_parameters_are_processmap_parameter_range_objects(self):
        """Test that returned parameters are ProcessMapParameterRange objects."""
        result = inputs_to_parameter_ranges(
            (["beam_power"], None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert all(isinstance(p, ProcessMapParameterRange) for p in result)

    def test_defaults_order_is_correct(self):
        """Test that default order is beam_power, scan_velocity, layer_height."""
        result = inputs_to_parameter_ranges(
            (None, None, None, None),
            (None, None, None, None),
            (None, None, None, None),
        )

        assert result[0].name == "beam_power"
        assert result[1].name == "scan_velocity"
        assert result[2].name == "layer_height"


class TestParameterRangeIntegration:
    """Integration tests for parameter range parsing."""

    def test_full_workflow_shorthand(self):
        """Test complete workflow with shorthand notation."""
        params = inputs_to_parameter_ranges(
            (["beam_power", "100", "1000", "100", "watts"], None, None, None),
            (["scan_velocity", "100", "2000", "100"], None, None, None),
            (["layer_height", "25", "100", "25"], None, None, None),
        )

        assert len(params) == 3

        # Verify beam_power
        assert params[0].name == "beam_power"
        assert params[0].start.magnitude == 100
        assert params[0].stop.magnitude == 1000
        assert params[0].step.magnitude == 100
        assert params[0].units == "watt"

        # Verify scan_velocity
        assert params[1].name == "scan_velocity"
        assert params[1].start.magnitude == 100
        assert params[1].stop.magnitude == 2000

        # Verify layer_height
        assert params[2].name == "layer_height"
        assert params[2].start.magnitude == 25

    def test_full_workflow_verbose(self):
        """Test complete workflow with verbose notation."""
        params = inputs_to_parameter_ranges(
            (None, "beam_power", [150, 900, 50], "watts"),
            (None, "scan_velocity", [200, 1800, 100], "millimeter / second"),
            (None, "layer_height", [30, 90, 30], "microns"),
        )

        assert len(params) == 3
        assert params[0].start.magnitude == 150
        assert params[1].start.magnitude == 200
        assert params[2].start.magnitude == 30

    def test_full_workflow_mixed(self):
        """Test complete workflow with mixed notation."""
        params = inputs_to_parameter_ranges(
            (["beam_power", "100", "1000", "50"], None, None, None),
            (None, "scan_velocity", None, None),  # Uses defaults
            (None, "layer_height", [30, 90, 30], None),
        )

        assert len(params) == 3
        assert params[0].start.magnitude == 100  # Custom
        assert params[1].start.magnitude == 100  # Default for scan_velocity
        assert params[2].start.magnitude == 30  # Custom
