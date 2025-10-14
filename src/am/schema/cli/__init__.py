from .__main__ import app

from .build_parameters import register_schema_build_parameters
from .material import register_schema_material
from .mesh_parameters import register_schema_mesh_parameters

_ = register_schema_build_parameters(app)
_ = register_schema_material(app)
_ = register_schema_mesh_parameters(app)

__all__ = ["app"]
