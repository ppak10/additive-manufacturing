from .__main__ import app
from .generate import register_slicer_generate

_ = register_slicer_generate(app)

__all__ = ["app"]
