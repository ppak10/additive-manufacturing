from .__main__ import workspace_app
from .initialize import register_workspace_initialize

_ = register_workspace_initialize(workspace_app)

__all__ = ["workspace_app"]
