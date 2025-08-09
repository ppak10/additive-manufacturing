from .__main__ import app
from .initialize import register_workspace_initialize
from .list import register_workspace_list

_ = register_workspace_initialize(app)
_ = register_workspace_list(app)

__all__ = ["app"]

