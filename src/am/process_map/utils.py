import numpy as np

from .models import ProcessMapPoints, ProcessMapPlotData


def process_map_points_to_plot_data(
    process_map_points: ProcessMapPoints,
) -> ProcessMapPlotData:
    """
    Converts 1D array of process map points to 2D or 3D parameters grid.
    Intended for organizing points to best plot values.
    Assumes uniform grid.
    """

    points = process_map_points.points

    # Assumes parameters are listed as [x, y, z]
    parameters = process_map_points.parameters

    axis_sets = [set() for parameter in parameters]

    # Creates axis sets.
    for point in points:
        for index, parameter in enumerate(parameters):
            value = point.build_parameters.__getattribute__(parameter)
            axis_set = axis_sets[index]

            if value not in axis_set:
                axis_set.add(value)

    # Sorts sets into lists for plotting.
    axis_lists = []

    # Creates index dictionary for fast reference when creating grid.
    axis_dict = {}
    for parameter in parameters:
        axis_dict[parameter] = {}

    # Sorts axes and creates index dictionary.
    for axis_set_index, axis_set in enumerate(axis_sets):
        parameter = parameters[axis_set_index]

        axis_list = sorted(list(axis_set))
        axis_lists.append(axis_list)

        for index, axis_item in enumerate(axis_list):
            axis_magnitude = axis_item.magnitude
            axis_dict[parameter][axis_magnitude] = index

    # Initialize grid with shape based on axis_lists
    shape = tuple(len(axis_list) for axis_list in axis_lists)
    grid = np.full(shape, None, dtype=object)

    # Populate grid in one loop
    for point in points:
        indices = tuple(
            axis_dict[param][point.build_parameters.__getattribute__(param).magnitude]
            for param in parameters
        )
        grid[indices] = point

    plot_data = ProcessMapPlotData(axes=axis_lists, grid=grid, parameters=parameters)

    return plot_data
