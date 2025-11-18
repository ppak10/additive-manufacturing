from .__main__ import app

from .build_parameters import register_config_build_parameters
from .material import register_config_material
from .mesh_parameters import register_config_mesh_parameters

_ = register_config_build_parameters(app)
_ = register_config_material(app)
_ = register_config_mesh_parameters(app)

__all__ = ["app"]
