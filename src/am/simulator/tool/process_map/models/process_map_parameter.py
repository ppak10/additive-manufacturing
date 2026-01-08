from pintdantic import QuantityDict, QuantityModel, QuantityField
from typing_extensions import TypedDict


class ProcessMapParameterDict(TypedDict):
    name: str
    value: QuantityDict


class ProcessMapParameter(QuantityModel):
    name: str
    value: QuantityField
