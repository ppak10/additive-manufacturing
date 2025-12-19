from .__main__ import app

# from .measure_melt_pool_dimensions import register_solver_measure_melt_pool_dimensions
from .run_layer import register_solver_run_layer
from .visualize import register_solver_visualize

_ = register_solver_run_layer(app)
_ = register_solver_visualize(app)
# _ = register_solver_measure_melt_pool_dimensions(app)

__all__ = ["app"]
