from mcp.server.fastmcp import FastMCP

from am.config.mcp import register_config
from am.process_map.mcp import (
    register_process_map_initialize_power_velocity_range,
    register_process_map_generate_process_map,
)
from am.slicer.mcp import register_slicer_slice
from am.solver.mcp import register_solver_run_layer, register_solver_visualize
from am.segmenter.mcp import (
    register_segmenter_parse,
    register_segmenter_shape_2d,
    register_segmenter_visualize_layer,
)
from am.workspace.mcp import register_workspace_create

app = FastMCP(name="additive-manufacturing")

_ = register_config(app)
_ = register_process_map_initialize_power_velocity_range(app)
_ = register_process_map_generate_process_map(app)
_ = register_segmenter_parse(app)
_ = register_segmenter_shape_2d(app)
_ = register_segmenter_visualize_layer(app)
_ = register_slicer_slice(app)
_ = register_solver_run_layer(app)
_ = register_solver_visualize(app)
_ = register_workspace_create(app)


def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()
