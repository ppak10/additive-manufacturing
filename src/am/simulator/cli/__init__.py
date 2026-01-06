from .__main__ import app

# from .measure_melt_pool_dimensions import register_solver_measure_melt_pool_dimensions
from .residual_heat import register_simulator_residual_heat 

_ = register_simulator_residual_heat(app)
# _ = register_solver_measure_melt_pool_dimensions(app)

__all__ = ["app"]
