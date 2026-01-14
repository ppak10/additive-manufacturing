from mcp.server.fastmcp import FastMCP


def register_simulator_tool_process_map(app: FastMCP):
    from pathlib import Path

    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    from am.simulator.tool.process_map.models import ProcessMap

    @app.tool(
        title="Generate Process Map",
        description="Generates process map of a given material over a range of build parameters",
        structured_output=True,
    )
    def simulator_tool_process_map(
        workspace_name: str,
        material_filename: str = "default.json",
        build_parameters_filename: str = "default.json",
        # Parameter 1
        p1_name: str | None = None,
        p1_range: list[int] | None = None,
        p1_units: str | None = None,
        # Parameter 2
        p2_name: str | None = None,
        p2_range: list[int] | None = None,
        p2_units: str | None = None,
        # Parameter 3
        p3_name: str | None = None,
        p3_range: list[int] | None = None,
        p3_units: str | None = None,
        num_proc: int = 1,
        visualize: bool = True,
    ) -> ToolSuccess[ProcessMap] | ToolError:
        """
        Generate a process map for additive manufacturing simulations.

        This tool runs simulations across a range of build parameters to create
        a process map that characterizes melt pool behavior under different
        processing conditions. The process map shows how varying parameters
        such as `beam_power`, `scan_velocity`, and `layer_height` affect
        the build quality and material properties.

        Parameter ranges (p1, p2, p3) are optional and will use defaults if not
        provided. However, if custom parameter ranges are specified, at minimum
        both p1 and p2 must be provided together (p3 remains optional).

        Args:
            workspace_name: Name of the workspace where simulation will be run
            material_filename: Filename of the material configuration (default: "default.json")
            build_parameters_filename: Filename of the build parameters configuration (default: "default.json")
            p1_name: Name of the first parameter to vary (e.g., "laser_power")
            p1_range: Range of values for the first parameter as [start, stop, step]
            p1_units: Units for the first parameter (e.g., "W")
            p2_name: Name of the second parameter to vary (e.g., "scan_speed")
            p2_range: Range of values for the second parameter as [start, stop, step]
            p2_units: Units for the second parameter (e.g., "mm/s")
            p3_name: Name of the third parameter to vary (optional)
            p3_range: Range of values for the third parameter as [start, stop, step]
            p3_units: Units for the third parameter
            num_proc: Number of parallel processes to use for simulation (default: 1)
            visualize: Whether to generate visualization plots of the process map (default: True)

        Returns:
            ToolSuccess[Path]: Path to the output folder containing simulation results and visualizations
            ToolError: Error information if the simulation fails

        Raises:
            PermissionError: If there are insufficient permissions to access workspace or run simulation
            Exception: If simulation fails for other reasons (invalid parameters, solver errors, etc.)
        """
        from am.config import BuildParameters, Material
        from am.simulator.tool.process_map.models import ProcessMap
        from am.simulator.tool.process_map.utils.parameter_ranges import (
            inputs_to_parameter_ranges,
        )
        from wa.cli.utils import get_workspace

        try:
            workspace = get_workspace(workspace_name)

            # Parse and validate parameters
            parameter_ranges = inputs_to_parameter_ranges(
                (None, p1_name, p1_range, p1_units),
                (None, p2_name, p2_range, p2_units),
                (None, p3_name, p3_range, p3_units),
            )

            # Load material and build parameters
            material = Material.load(
                workspace.path / "configs" / "materials" / material_filename
            )

            build_parameters = BuildParameters.load(
                workspace.path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            # Create output folder
            process_map_path = Path("simulations/process_map") / material.name
            workspace_folder = workspace.create_folder(
                name_or_path=process_map_path,
                append_timestamp=True,
            )

            # Create ProcessMap
            process_map = ProcessMap(
                build_parameters=build_parameters,
                material=material,
                parameter_ranges=parameter_ranges,
                out_path=workspace_folder.path,
            )

            process_map.run(num_proc=num_proc)

            if visualize:
                process_map.plot()

            process_map.save()

            return tool_success(process_map)

        except PermissionError as e:
            return tool_error(
                "Permission denied when running solver",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to run solver",
                "SOLVER_RUN_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

        _ = simulator_tool_process_map
