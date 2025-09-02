from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_schema_material(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.schema import QuantityInput
    from am.schema.material import DEFAULT

    @app.tool(
        title="Material Schema",
        description="Creates a configuration file for material properties such as temperature, absorptivity, density, etc.",
        structured_output=True,
    )
    async def schema_material(
        workspace: str,
        name: str = "default",
        specific_heat_capacity: QuantityInput | None = DEFAULT[
            "specific_heat_capacity"
        ],
        absorptivity: QuantityInput | None = DEFAULT["absorptivity"],
        thermal_conductivity: QuantityInput | None = DEFAULT["thermal_conductivity"],
        density: QuantityInput | None = DEFAULT["density"],
        temperature_melt: QuantityInput | None = DEFAULT["temperature_melt"],
        temperature_liquidus: QuantityInput | None = DEFAULT["temperature_liquidus"],
        temperature_solidus: QuantityInput | None = DEFAULT["temperature_solidus"],
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Creates a configuration file for material properties.
        Args:
            workspace: Folder name of existing workspace.
            name: Used in generating file name for saved material properties
            specific_heat_capacity: Defaults to 455 joules / (kilogram * kelvin)
            absorptivity: Defaults to 1.0 dimensionless
            thermal_conductivity: Defaults to 8.9 watts / (meter * kelvin)
            density: Defaults to 7910 kilogram / (meter) ** 3
            temperature_melt: Defaults to 1673 kelvin
            temperature_liquidus: Defaults to 1710.26 kelvin
            temperature_solidus: Defaults to 1683.68 kelvin
        """

        from am.cli.utils import get_workspace_path
        from am.schema import Material

        try:
            workspace_path = get_workspace_path(workspace)
            material = Material(
                name=name,
                specific_heat_capacity=specific_heat_capacity,
                absorptivity=absorptivity,
                thermal_conductivity=thermal_conductivity,
                density=density,
                temperature_melt=temperature_melt,
                temperature_liquidus=temperature_liquidus,
                temperature_solidus=temperature_solidus,
            )
            save_path = workspace_path / "materials" / f"{name}.json"
            material.save(save_path)

            return tool_success(save_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating Material file.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create Material file",
                "SCHEMA_MATERIAL_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = schema_material
