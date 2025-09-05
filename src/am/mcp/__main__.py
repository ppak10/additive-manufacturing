from mcp.server.fastmcp import FastMCP

from am.solver.mcp import register_solver
from am.process_map.mcp import (
    register_process_map_initialize_power_velocity_range,
    register_process_map_generate_process_map,
)
from am.schema.mcp import register_schema_build_parameters, register_schema_material
from am.segmenter.mcp import (
    register_segmenter_parse,
    register_segmenter_shape_2d,
    register_segmenter_visualize_layer,
)
from am.workspace.mcp import (
    register_workspace_initialize,
    register_workspace_list,
    register_workspace_list_resources,
)

app = FastMCP(name="additive-manufacturing")

_ = register_process_map_initialize_power_velocity_range(app)
_ = register_process_map_generate_process_map(app)
_ = register_schema_build_parameters(app)
_ = register_schema_material(app)
_ = register_segmenter_parse(app)
_ = register_segmenter_shape_2d(app)
_ = register_segmenter_visualize_layer(app)
_ = register_solver(app)
_ = register_workspace_initialize(app)
_ = register_workspace_list(app)
_ = register_workspace_list_resources(app)


def main():
    """Entry point for the direct execution server."""
    app.run()


if __name__ == "__main__":
    main()
