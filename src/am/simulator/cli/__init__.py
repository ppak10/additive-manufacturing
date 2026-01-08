from .__main__ import app

# from .measure_melt_pool_dimensions import register_solver_measure_melt_pool_dimensions
from .process_map import register_simulator_process_map
from .residual_heat import register_simulator_residual_heat

_ = register_simulator_process_map(app)
_ = register_simulator_residual_heat(app)
# _ = register_solver_measure_melt_pool_dimensions(app)

__all__ = ["app"]
