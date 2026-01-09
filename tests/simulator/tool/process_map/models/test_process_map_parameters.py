import pytest
from am.simulator.tool.process_map.models.process_map_parameter_range import (
    ProcessMapParameterRange,
    DEFAULTS,
)


class TestProcessMapParameterRangeDefaults:
    """Test that defaults are applied correctly based on parameter name."""

    def test_beam_power_defaults(self):
        """Test beam_power gets correct defaults."""
        param = ProcessMapParameterRange(name="beam_power")

        assert param.name == "beam_power"
        assert param.start.magnitude == 100
        assert str(param.start.units) == "watt"
        assert param.stop.magnitude == 1000
        assert str(param.stop.units) == "watt"
        assert param.step.magnitude == 100
        assert str(param.step.units) == "watt"
        assert param.units == "watt"

    def test_scan_velocity_defaults(self):
        """Test scan_velocity gets correct defaults."""
        param = ProcessMapParameterRange(name="scan_velocity")

        assert param.name == "scan_velocity"
        assert param.start.magnitude == 100
        assert str(param.start.units) == "millimeter / second"
        assert param.stop.magnitude == 2000
        assert str(param.stop.units) == "millimeter / second"
        assert param.step.magnitude == 100
        assert str(param.step.units) == "millimeter / second"
        assert param.units == "millimeter / second"

    def test_layer_height_defaults(self):
        """Test layer_height gets correct defaults."""
        param = ProcessMapParameterRange(name="layer_height")

        assert param.name == "layer_height"
        assert param.start.magnitude == 25
        assert str(param.start.units) == "micron"
        assert param.stop.magnitude == 100
        assert str(param.stop.units) == "micron"
        assert param.step.magnitude == 25
        assert str(param.step.units) == "micron"
        assert param.units == "micron"


class TestProcessMapParameterRangeOverrides:
    """Test that defaults can be overridden."""

    def test_override_start_only(self):
        """Test overriding only start value."""
        param = ProcessMapParameterRange(name="beam_power", start=(50, "watts"))

        assert param.start.magnitude == 50
        assert str(param.start.units) == "watt"
        # Stop and step should still use defaults
        assert param.stop.magnitude == 1000
        assert param.step.magnitude == 100
        assert param.units == "watt"

    def test_override_stop_only(self):
        """Test overriding only stop value."""
        param = ProcessMapParameterRange(name="beam_power", stop=(1500, "watts"))

        assert param.stop.magnitude == 1500
        assert str(param.stop.units) == "watt"
        # Start and step should still use defaults
        assert param.start.magnitude == 100
        assert param.step.magnitude == 100
        assert param.units == "watt"

    def test_override_step_only(self):
        """Test overriding only step value."""
        param = ProcessMapParameterRange(name="beam_power", step=(50, "watts"))

        assert param.step.magnitude == 50
        assert str(param.step.units) == "watt"
        # Start and stop should still use defaults
        assert param.start.magnitude == 100
        assert param.stop.magnitude == 1000
        assert param.units == "watt"

    def test_override_all_values(self):
        """Test overriding all values."""
        param = ProcessMapParameterRange(
            name="beam_power",
            start=(200, "watts"),
            stop=(800, "watts"),
            step=(50, "watts"),
        )

        assert param.start.magnitude == 200
        assert param.stop.magnitude == 800
        assert param.step.magnitude == 50
        assert str(param.start.units) == "watt"
        assert param.units == "watt"

    def test_override_with_consistent_different_units(self):
        """Test overriding all values with different but consistent units."""
        param = ProcessMapParameterRange(
            name="scan_velocity",
            start=(0.1, "meter / second"),
            stop=(2.0, "meter / second"),
            step=(0.1, "meter / second"),
        )

        # Should accept different units as long as they're consistent
        assert param.start.magnitude == 0.1
        assert str(param.start.units) == "meter / second"
        assert str(param.stop.units) == "meter / second"
        assert str(param.step.units) == "meter / second"
        assert param.units == "meter / second"


class TestProcessMapParameterRangeValidation:
    """Test parameter name and units validation."""

    def test_invalid_parameter_name_raises_error(self):
        """Test that invalid parameter names raise ValueError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ProcessMapParameterRange(name="custom_parameter")

        # Check that the error message mentions valid parameter names
        assert "Invalid parameter name" in str(exc_info.value)

    def test_mismatched_units_raises_error(self):
        """Test that mismatched units between start/stop/step raise ValueError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ProcessMapParameterRange(
                name="beam_power",
                start=(100, "watts"),
                stop=(1000, "kilowatts"),  # Different unit!
                step=(100, "watts"),
            )

        assert "All fields must have the same units" in str(exc_info.value)

    def test_mismatched_step_units_raises_error(self):
        """Test that mismatched step units raise ValueError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ProcessMapParameterRange(
                name="beam_power",
                start=(100, "watts"),
                stop=(1000, "watts"),
                step=(100, "kilowatts"),  # Different unit!
            )

        assert "All fields must have the same units" in str(exc_info.value)

    def test_invalid_parameter_name_with_values_raises_error(self):
        """Test that invalid parameter names raise error even with explicit values."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError) as exc_info:
            ProcessMapParameterRange(
                name="custom_parameter",
                start=(10, "celsius"),
                stop=(100, "celsius"),
                step=(5, "celsius"),
            )

        assert "Invalid parameter name" in str(exc_info.value)

    def test_all_default_names_are_valid(self):
        """Test that all names in DEFAULTS are valid."""
        for param_name in DEFAULTS.keys():
            # Should not raise any error
            param = ProcessMapParameterRange(name=param_name)
            assert param.name == param_name
            # Units field should be accessible
            assert param.units is not None

    def test_empty_string_name_raises_error(self):
        """Test that empty string name raises ValueError."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ProcessMapParameterRange(
                name="",
                start=(1, "dimensionless"),
                stop=(10, "dimensionless"),
                step=(1, "dimensionless"),
            )


class TestProcessMapParameterRangeDictInput:
    """Test that dict input works correctly."""

    def test_dict_with_defaults(self):
        """Test creating from dict with name only."""
        data = {"name": "beam_power"}
        param = ProcessMapParameterRange(**data)

        assert param.start.magnitude == 100
        assert param.stop.magnitude == 1000
        assert param.step.magnitude == 100
        assert param.units == "watt"

    def test_dict_with_partial_override(self):
        """Test creating from dict with partial values."""
        data = {"name": "beam_power", "start": (150, "watts")}
        param = ProcessMapParameterRange(**data)

        assert param.start.magnitude == 150
        assert param.stop.magnitude == 1000  # From defaults
        assert param.step.magnitude == 100  # From defaults
        assert param.units == "watt"


class TestProcessMapParameterRangeUnitsField:
    """Test the read-only units field."""

    def test_units_field_from_defaults(self):
        """Test that units field is correctly derived from step field."""
        param = ProcessMapParameterRange(name="beam_power")
        assert param.units == "watt"
        assert param.units == str(param.step.units)

    def test_units_field_with_custom_values(self):
        """Test that units field updates with custom step values."""
        param = ProcessMapParameterRange(
            name="scan_velocity",
            start=(100, "millimeter / second"),
            stop=(1000, "millimeter / second"),
            step=(50, "millimeter / second"),
        )
        assert param.units == "millimeter / second"

    def test_units_field_is_read_only(self):
        """Test that units field cannot be set directly."""
        param = ProcessMapParameterRange(name="beam_power")

        # Attempting to set units should fail (it's a computed property)
        with pytest.raises(AttributeError):
            param.units = "kilowatts"

    def test_units_matches_all_fields(self):
        """Test that units field matches all quantity fields."""
        param = ProcessMapParameterRange(name="layer_height")

        assert param.units == str(param.start.units)
        assert param.units == str(param.stop.units)
        assert param.units == str(param.step.units)


class TestProcessMapParameterRangeEdgeCases:
    """Test edge cases and special scenarios."""

    def test_all_defaults_are_valid(self):
        """Test that all defaults in DEFAULTS dict are valid."""
        for param_name in DEFAULTS.keys():
            param = ProcessMapParameterRange(name=param_name)
            assert param.name == param_name
            assert param.start is not None
            assert param.stop is not None
            assert param.step is not None
            assert param.units is not None

    def test_all_default_parameters_exist(self):
        """Test that expected default parameters exist."""
        expected_params = [
            "beam_power",
            "scan_velocity",
            "layer_height",
            "hatch_spacing",
            "beam_diameter",
            "temperature_preheat",
        ]

        for param_name in expected_params:
            assert param_name in DEFAULTS
