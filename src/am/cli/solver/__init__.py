from .__main__ import solver_app
from .initialize import register_solver_initialize
from .initialize_build_config import register_solver_initialize_build_config
from .initialize_mesh_config import register_solver_initialize_mesh_config
from .initialize_material_config import register_solver_initialize_material_config
from .run_layer import register_solver_run_layer
from .visualize import register_solver_visualize

# from .parse import register_solver_parse

_ = register_solver_initialize(solver_app)
_ = register_solver_initialize_build_config(solver_app)
_ = register_solver_initialize_material_config(solver_app)
_ = register_solver_initialize_mesh_config(solver_app)
_ = register_solver_run_layer(solver_app)
_ = register_solver_visualize(solver_app)
# _ = register_solver_parse(solver_app)

__all__ = ["solver_app"]
