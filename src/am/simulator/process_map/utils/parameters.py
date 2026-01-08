from pint import Quantity
from typing_extensions import cast

from am.simulator.process_map.models.process_map_parameters import (
    DEFAULTS,
    ProcessMapParameter,
    ProcessMapParameterInputTuple,
)


def parse_shorthand(values: list[str] | None) -> ProcessMapParameter | None:
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
        parameter = ProcessMapParameter(name=name)
    else:
        raise Exception(f"parameter name: {name} is invalid.")

    # Obtain units from instantiated parameter
    if units is None:
        units = parameter.units

    # If we have 2 numeric values, they will be start and stop
    if numeric_values is not None and len(numeric_values) >= 2:
        parameter.start = cast(Quantity, Quantity(numeric_values[0], units))
        parameter.stop = cast(Quantity, Quantity(numeric_values[1], units))

    if numeric_values and len(numeric_values) >= 3:
        parameter.step = cast(Quantity, Quantity(numeric_values[2], units))

    return parameter


def parse_options(
    shorthand: list[str] | None,
    name: str | None,
    range_values: list[int] | None,
    units: str | None,
) -> ProcessMapParameter | None:
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
            parameter = ProcessMapParameter(name=name)
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


def inputs_to_parameters(*input_tuples: ProcessMapParameterInputTuple):
    """
    Parse and validate parameters from CLI input.

    If no parameters are provided, uses defaults in order:
    1. beam_power
    2. scan_velocity
    3. layer_height

    Args:
        parameter_tuples: List of tuples containing (shorthand, name, range_vals, units)
        verbose: Whether to print verbose output

    Returns:
        List of ProcessMapParameter objects

    Raises:
        typer.Exit: If validation fails
    """
    from am.simulator.process_map.models import ProcessMapParameter
    from am.simulator.process_map.models.process_map_parameters import DEFAULTS

    parameters = []

    # If no parameters provided, use defaults in order
    if all(all(v is None for v in param) for param in input_tuples):

        # Should be just "beam_power", "scan_velocity", and "layer_height"
        keys = list(DEFAULTS.keys())[:3]

        for key in keys:
            parameter = ProcessMapParameter(name=key)
            parameters.append(parameter)

        return parameters

    for shorthand, name, range_values, units in input_tuples:
        parameter = parse_options(shorthand, name, range_values, units)

        if parameter is not None:
            parameters.append(parameter)

    return parameters
