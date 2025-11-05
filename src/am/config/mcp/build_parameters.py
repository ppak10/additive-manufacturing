from mcp.server.fastmcp import FastMCP

from pathlib import Path
from typing import Union


def register_config_build_parameters(app: FastMCP):
    from pintdantic import QuantityInput

    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.config.build_parameters import DEFAULT

    @app.tool(
        title="Generate Build Parameters Configuration File",
        description="Creates a configuration file for build parameters such as beam_diameter, beam_power, scan_velocity, and temperature_preheat",
        structured_output=True,
    )
    async def config_build_parameters(
        workspace: str,
        name: str | None = "default",
        beam_diameter: QuantityInput | None = DEFAULT["beam_diameter"],
        beam_power: QuantityInput | None = DEFAULT["beam_power"],
        hatch_spacing: QuantityInput | None = DEFAULT["hatch_spacing"],
        layer_height: QuantityInput | None = DEFAULT["layer_height"],
        scan_velocity: QuantityInput | None = DEFAULT["scan_velocity"],
        temperature_preheat: QuantityInput | None = DEFAULT["temperature_preheat"],
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Creates a configuration file for build parameters.
        Args:
            workspace: Folder name of existing workspace.
            name: Used in generating file name for saved build parameters
            beam_diameter: Defaults to 5e-5 meters
            beam_power: Defaults to 200 watts
            hatch_spacing: Defaults to 50 microns
            layer_height: Defaults to 100 microns
            scan_velocity: Defaults to 0.8 meters / second
            temperature_preheat: Defaults to 300 kelvin
        """

        from am.config import BuildParameters

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace)
            build_parameters = BuildParameters(
                beam_diameter=beam_diameter,
                beam_power=beam_power,
                hatch_spacing=hatch_spacing,
                layer_height=layer_height,
                scan_velocity=scan_velocity,
                temperature_preheat=temperature_preheat,
            )
            save_path = workspace_path / "config" / "build_parameters" / f"{name}.json"
            build_parameters.save(save_path)

            return tool_success(save_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when creating Build Parameters file.",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to create Build Parameters file",
                "CONFIG_BUILD_PARAMETERS_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = config_build_parameters
