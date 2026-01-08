from pydantic import BaseModel


class ProcessMapPointLabels(BaseModel):
    """
    Labels of potential behaviors within a point on the process map due to a
    combination of process parameters.
    """

    lack_of_fusion: bool | None = None
    keyholing: bool | None = None
    balling: bool | None = None
