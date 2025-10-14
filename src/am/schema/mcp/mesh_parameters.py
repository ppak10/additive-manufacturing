from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_schema_mesh_parameters(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.schema import QuantityInput
    from am.schema.mesh_parameters import DEFAULT

    @app.tool(
        title="Mesh Parameters Schema",
        description="Creates a configuration file for mesh parameters such as step sizes, bounds, initial positions, and padding",
        structured_output=True,
    )
    async def schema_mesh_parameters(
        workspace: str,
        name: str | None = "default",
        x_step: QuantityInput | None = DEFAULT["x_step"],
        y_step: QuantityInput | None = DEFAULT["y_step"],
        z_step: QuantityInput | None = DEFAULT["z_step"],
        x_min: QuantityInput | None = DEFAULT["x_min"],
        x_max: QuantityInput | None = DEFAULT["x_max"],
        y_min: QuantityInput | None = DEFAULT["y_min"],
        y_max: QuantityInput | None = DEFAULT["y_max"],
        z_min: QuantityInput | None = DEFAULT["z_min"],
        z_max: QuantityInput | None = DEFAULT["z_max"],
        x_initial: QuantityInput | None = DEFAULT["x_initial"],
        y_initial: QuantityInput | None = DEFAULT["y_initial"],
        z_initial: QuantityInput | None = DEFAULT["z_initial"],
        x_start_pad: QuantityInput | None = DEFAULT["x_start_pad"],
        y_start_pad: QuantityInput | None = DEFAULT["y_start_pad"],
        z_start_pad: QuantityInput | None = DEFAULT["z_start_pad"],
        x_end_pad: QuantityInput | None = DEFAULT["x_end_pad"],
        y_end_pad: QuantityInput | None = DEFAULT["y_end_pad"],
        z_end_pad: QuantityInput | None = DEFAULT["z_end_pad"],
        boundary_condition: str | None = "temperature",
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Creates a configuration file for mesh parameters.
        Args:
            workspace: Folder name of existing workspace.
            name: Used in generating file name for saved mesh parameters
            x_step: Defaults to 25 micrometers
            y_step: Defaults to 25 micrometers
            z_step: Defaults to 25 micrometers
            x_min: Defaults to 0.0 millimeters
            x_max: Defaults to 10.0 millimeters
            y_min: Defaults to 0.0 millimeters
            y_max: Defaults to 10.0 millimeters
            z_min: Defaults to -0.8 millimeters
            z_max: Defaults to 0.0 millimeters
            x_initial: Defaults to 0.0 millimeters
            y_initial: Defaults to 0.0 millimeters
            z_initial: Defaults to 0.0 millimeters
            x_start_pad: Defaults to 0.2 millimeters
            y_start_pad: Defaults to 0.2 millimeters
            z_start_pad: Defaults to 0.0 millimeters
            x_end_pad: Defaults to 0.2 millimeters
            y_end_pad: Defaults to 0.2 millimeters
            z_end_pad: Defaults to 0.1 millimeters
            boundary_condition: Defaults to "temperature"
        """

        from am.schema import MeshParameters

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace)
            mesh_parameters = MeshParameters(
                x_step=x_step,
                y_step=y_step,
                z_step=z_step,
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
                z_min=z_min,
                z_max=z_max,
                x_initial=x_initial,
                y_initial=y_initial,
                z_initial=z_initial,
                x_start_pad=x_start_pad,
                y_start_pad=y_start_pad,
                z_start_pad=z_start_pad,
                x_end_pad=x_end_pad,
                y_end_pad=y_end_pad,
                z_end_pad=z_end_pad,
                boundary_condition=boundary_condition,
            )
            save_path = workspace_path / "mesh_parameters" / f"{name}.json"
            mesh_parameters.save(save_path)

            return tool_success(save_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating Mesh Parameters file.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create Mesh Parameters file",
                "SCHEMA_MESH_PARAMETERS_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = schema_mesh_parameters
