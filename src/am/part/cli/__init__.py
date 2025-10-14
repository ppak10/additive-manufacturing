from .__main__ import app
from .initialize import register_part_initialize

_ = register_part_initialize(app)

__all__ = ["app"]
