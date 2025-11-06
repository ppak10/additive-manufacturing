from .__main__ import app
from .initialize import register_workspace_initialize

_ = register_workspace_initialize(app)

__all__ = ["app"]
