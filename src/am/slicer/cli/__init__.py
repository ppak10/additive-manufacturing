from .__main__ import app
from .slice import register_slicer_slice

_ = register_slicer_slice(app)

__all__ = ["app"]
