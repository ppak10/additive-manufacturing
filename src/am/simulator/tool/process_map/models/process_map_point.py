from pydantic import BaseModel

from .melt_pool_dimensions import MeltPoolDimensions
from .process_map_parameter import ProcessMapParameter
from .process_map_point_labels import ProcessMapPointLabels


class ProcessMapPoint(BaseModel):
    """
    Extends Build Parameters for process map point.
    """

    parameters: list[ProcessMapParameter]
    melt_pool_dimensions: MeltPoolDimensions
    labels: ProcessMapPointLabels
