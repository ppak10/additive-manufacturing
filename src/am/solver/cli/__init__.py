from .__main__ import app
from .initialize import register_solver_initialize
from .initialize_build_config import register_solver_initialize_build_config
from .initialize_mesh_config import register_solver_initialize_mesh_config
from .initialize_material_config import register_solver_initialize_material_config
from .run_layer import register_solver_run_layer
from .visualize import register_solver_visualize

_ = register_solver_initialize(app)
_ = register_solver_initialize_build_config(app)
_ = register_solver_initialize_material_config(app)
_ = register_solver_initialize_mesh_config(app)
_ = register_solver_run_layer(app)
_ = register_solver_visualize(app)

__all__ = ["app"]
