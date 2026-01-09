from pydantic import BaseModel
from typing import Literal, TypeAlias

from am.simulator.solver.models import MeltPoolDimensions

from .process_map_parameter import ProcessMapParameter

from pydantic import BaseModel

ProcessMapDataPointLabel: TypeAlias = Literal["lack_of_fusion", "keyholing", "balling"]


class ProcessMapDataPoint(BaseModel):
    """
    Data point referenced within ProcessMap object
    (flattened list, independent of dimension).

    Provides an override of build parameters to use for calculating potential
    process map labels, with `labels` and `melt_pool_dimensions` as None.

    These values are then updated with their respective values one data is
    obtained.
    """

    parameters: list[ProcessMapParameter]
    melt_pool_dimensions: MeltPoolDimensions | None = None
    labels: list[ProcessMapDataPointLabel] | None = None
