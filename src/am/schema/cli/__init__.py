from .__main__ import app

from .build_parameters import register_schema_build_parameters
from .material import register_schema_material

_ = register_schema_build_parameters(app)
_ = register_schema_material(app)

__all__ = ["app"]
