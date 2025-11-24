from .__main__ import app

from .create import register_process_map_create
from .plot import register_process_map_plot
from .run import register_process_map_run

register_process_map_create(app)
register_process_map_plot(app)
register_process_map_run(app)

__all__ = ["app"]
