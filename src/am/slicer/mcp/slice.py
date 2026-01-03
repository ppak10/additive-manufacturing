from mcp.server.fastmcp import FastMCP

def register_slicer_slice(app: FastMCP):

    from datetime import datetime
    from mcp.server.fastmcp import Context
    from pathlib import Path
    from typing import Union

    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.slicer.format import Format

    @app.tool(
        title="Slice Part",
        description="Slice an stl part within the `parts` subfolder for a given layer height (mm) and hatch spacing (mm)",
        structured_output=True,
    )
    async def slicer_slice(
        ctx: Context,
        part_filename: str,
        workspace_name: str,
        layer_height: float | None = None,
        hatch_spacing: float | None = None,
        build_parameters_filename: str = "default.json",
        binary: bool = False,
        format: Format = "solver",
        visualize: bool = True,
        num_proc: int = 1,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Slice an stl part within a given workspace.

        Task List:
        1. Load Build Build Parameters 
        2. Load Part Mesh
        3. Create slice geometries
        4. Convert geometries to output format (Optional)
        5. Visualize outputs (Optional)

        Args:
            ctx: Context for long running task
            part_filename: Name of 3D model file to slice, should be `.stl` format.
            workspace_name: Folder name of existing workspace.
            layer_height: Optional layer height override (mm).
            hatch_spacing: Optional hatch spacing override (mm).
            build_parameters_filename: Used as the base setting for slicer.
            binary: Generate output files as binary rather than text.
            format: Output format for slicer such as solver or gcode.
            visualize: Generate visualizations of sliced layers.
            num_proc: Enable multiprocessing by specifying number of processes to use.
        """
        # TODO: #6 Support "in" stl mesh units.
        # mesh_units: Units 3D part file is defined in (i.e. "in" or "mm")

        from am.config import BuildParameters
        from am.slicer.models import Slicer

        from wa.cli.utils import get_workspace

        workspace = get_workspace(workspace_name)

        try:
            part_path = workspace.path / "parts" / part_filename

            build_parameters = BuildParameters.load(
                workspace.path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            workspace_folder = workspace.create_folder(
                name_or_path = Path("toolpaths") / part_path.stem,
                append_timestamp = True,
            )

            async def progress_callback(current: int, total: int):
                await ctx.report_progress(progress=current, total=total)

            slicer = Slicer(
                build_parameters=build_parameters,
                out_path=workspace_folder.path,
                progress_callback=progress_callback,
            )

            # Load mesh (0-10%)
            await ctx.report_progress(progress=0, total=100)
            slicer.load_mesh(part_path)
            await ctx.report_progress(progress=10, total=100)

            # Section mesh (10-20%)
            slicer.section_mesh(layer_height=layer_height)
            await ctx.report_progress(progress=20, total=100)

            # Generate slices (20-50%)
            await slicer.slice_sections(
                hatch_spacing=hatch_spacing, binary=binary, num_proc=num_proc
            )
            await ctx.report_progress(progress=50, total=100)

            # Export to solver format if requested (50-70%)
            if format == "solver":
                solver_data_out_path = await slicer.export_solver_segments(
                    binary=binary, num_proc=num_proc
                )
                await ctx.report_progress(progress=70, total=100)

            # Visualize if requested (70-100% or 50-100% if no export)
            if visualize:
                visualizations_path = await slicer.visualize_slices(
                    binary=binary, num_proc=num_proc
                )
                await ctx.report_progress(progress=100, total=100)
                return tool_success(visualizations_path)

            await ctx.report_progress(progress=100, total=100)
            slicer.save()  # Save configuration to slicer.json
            return tool_success(
                solver_data_out_path if format == "solver" else workspace_path / "toolpaths" / run_name
            )

        except PermissionError as e:
            return tool_error(
                "Permission denied when slicing part",
                "PERMISSION_DENIED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to slice part",
                "SLICER_SLICE_FAILED",
                workspace_name=workspace_name,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = slicer_slice
