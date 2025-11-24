from .__main__ import app

from .build_parameters import register_config_build_parameters
from .material import register_config_material
from .mesh_parameters import register_config_mesh_parameters
from .process_map import register_config_process_map

_ = register_config_build_parameters(app)
_ = register_config_material(app)
_ = register_config_mesh_parameters(app)
_ = register_config_process_map(app)

__all__ = ["app"]
