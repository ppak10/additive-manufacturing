from .__main__ import app
from .create import register_workspace_create

_ = register_workspace_create(app)

__all__ = ["app"]
