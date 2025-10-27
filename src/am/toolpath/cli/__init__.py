from .__main__ import app
from .generate import register_toolpath_generate

_ = register_toolpath_generate(app)

__all__ = ["app"]
