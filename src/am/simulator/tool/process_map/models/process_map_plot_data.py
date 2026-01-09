import numpy as np

from pydantic import BaseModel, ConfigDict
from pint import Quantity
from typing_extensions import ClassVar


class ProcessMapPlotData(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    parameter_names: list[str] = []
    grid: np.ndarray
    axes: list[list[Quantity]]
