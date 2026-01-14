from pint import Quantity
from typing_extensions import cast

from am.simulator.tool.process_map.models.process_map_parameter_range import (
    DEFAULTS,
    ProcessMapParameterRange,
    ProcessMapParameterRangeInputTuple,
)


def parse_shorthand(values: list[str] | None) -> ProcessMapParameterRange | None:
    """
    Parse shorthand parameter notation: --p1 beam_power 100 1000 100 watts

    Format: <name> [<min> <max> <step>] [<units>]
    Only <name> is required.
    """
    if not values or len(values) == 0:
        return None

    # First value is always the name
    name = values[0]

    # Try to parse numeric values for min/max/step
    numeric_values = []
    units = None

    for val in values[1:]:
        try:
            numeric_values.append(int(val))
        except ValueError:
            # Non-numeric value is likely units
            units = val
            break

    if name in DEFAULTS.keys():
        # Initialize with defaults
        parameter_range = ProcessMapParameterRange(name=name)
    else:
        raise Exception(f"parameter name: {name} is invalid.")

    # Obtain units from instantiated parameter
    if units is None:
        units = parameter_range.units

    # If we have 2 numeric values, they will be start and stop
    if numeric_values is not None and len(numeric_values) >= 2:
        parameter_range.start = cast(Quantity, Quantity(numeric_values[0], units))
        parameter_range.stop = cast(Quantity, Quantity(numeric_values[1], units))

    if numeric_values and len(numeric_values) >= 3:
        parameter_range.step = cast(Quantity, Quantity(numeric_values[2], units))

    return parameter_range


def parse_options(
    shorthand: list[str] | None,
    name: str | None,
    range_values: list[int] | None,
    units: str | None,
) -> ProcessMapParameterRange | None:
    """
    Merge shorthand and verbose parameter options.
    Verbose options take precedence over shorthand.
    """
    # Start with shorthand parsing
    parameter = parse_shorthand(shorthand)

    # If shorthand is not provided
    if not parameter:
        if name in DEFAULTS.keys():
            # Initialize with defaults
            parameter = ProcessMapParameterRange(name=name)
        else:
            return None

    # Shorthand provided along with name override
    elif name is not None:
        parameter.name = name

    # Obtain units from instantiated parameter
    if units is None:
        units = parameter.units

    # If we have 2 numeric values, they're min and max
    if range_values is not None and len(range_values) >= 2:
        parameter.start = cast(Quantity, Quantity(range_values[0], units))
        parameter.stop = cast(Quantity, Quantity(range_values[1], units))

    if range_values and len(range_values) >= 3:
        parameter.step = cast(Quantity, Quantity(range_values[2], units))

    return parameter


def inputs_to_parameter_ranges(*input_tuples: ProcessMapParameterRangeInputTuple):
    """
    Parse and validate parameter ranges from CLI input.

    If no parameters are provided, uses defaults in order:
    1. beam_power
    2. scan_velocity
    3. layer_height

    Args:
        input_tuples: List of tuples containing (shorthand, name, range_vals, units)
        verbose: Whether to print verbose output

    Returns:
        List of ProcessMapParameterRange objects

    Raises:
        typer.Exit: If validation fails
    """
    parameter_ranges = []

    # If no parameters provided, use defaults in order
    if all(all(v is None for v in param) for param in input_tuples):

        # Should be just "beam_power", "scan_velocity", and "layer_height"
        keys = list(DEFAULTS.keys())[:3]

        for key in keys:
            parameter_range = ProcessMapParameterRange(name=key)
            parameter_ranges.append(parameter_range)

        return parameter_ranges

    for shorthand, name, range_values, units in input_tuples:
        parameter_range = parse_options(shorthand, name, range_values, units)

        if parameter_range is not None:
            parameter_ranges.append(parameter_range)

    return parameter_ranges
