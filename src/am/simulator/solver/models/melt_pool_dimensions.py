# TODO: Refactor
import json

from pathlib import Path
from pint import Quantity
from pydantic import ValidationError
from pintdantic import QuantityDict, QuantityModel, QuantityField
from typing_extensions import cast, TypedDict

######################
# MeltPoolDimensions #
######################


class MeltPoolDimensionsDict(TypedDict):
    depth: QuantityDict
    width: QuantityDict
    length: QuantityDict
    length_front: QuantityDict
    length_behind: QuantityDict


class MeltPoolDimensions(QuantityModel):
    """Melt pool dimensions from simulation."""

    depth: QuantityField
    width: QuantityField
    length: QuantityField
    length_front: QuantityField
    length_behind: QuantityField

    def to_dict(self, verbose: bool = False) -> MeltPoolDimensionsDict | dict:
        """
        Convert to dictionary format.

        Args:
            verbose: If True, use verbose dict format. If False, use condensed list format (default)

        Returns:
            Dictionary representation (format depends on verbose flag)
        """
        return self.model_dump(context={"verbose": verbose})

    @classmethod
    def from_dict(cls, data: MeltPoolDimensionsDict) -> "MeltPoolDimensions":
        """Create from dictionary (supports both verbose and condensed formats)."""
        return cls(**data)
