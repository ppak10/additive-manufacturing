from .base import WorkspaceBase
from .segmenter.gcode import WorkspaceSegmenterGCode
from .segmenter.utils import WorkspaceSegmenterUtils
from .simulation.base import WorkspaceSimulationBase
from .simulation.utils import WorkspaceSimulationUtils
from .solver.base import WorkspaceSolverBase
from .solver.utils import WorkspaceSolverUtils
from .utils import WorkspaceUtils

class Workspace(
    WorkspaceBase,
    WorkspaceSegmenterGCode,
    WorkspaceSegmenterUtils,
    WorkspaceSimulationBase,
    WorkspaceSimulationUtils,
    WorkspaceSolverBase,
    WorkspaceSolverUtils,
    WorkspaceUtils
):
    def __init__(
            self,
            name: str = None,
            filename: str = None,
            workspace_path: str = None,
            verbose = False,
            **kwargs,
        ):
        super().__init__(
            name = name,
            filename = filename,
            verbose = verbose,
            workspace_path = workspace_path,
            **kwargs,
        )
