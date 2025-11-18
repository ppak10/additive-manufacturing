from mcp.server.fastmcp import FastMCP, Context

from datetime import datetime
from pathlib import Path
from typing import Union


def register_slicer_slice(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error

    @app.tool(
        title="Slicer slice",
        description="Slice an stl part within the `parts` subfolder for a given layer height (mm) and hatch spacing (mm)",
        structured_output=True,
    )
    async def slicer_slice(
        ctx: Context,
        filename: str,
        workspace_name: str,
        layer_height: float | None = None,
        hatch_spacing: float | None = None,
        build_parameters_filename: str = "default.json",
        binary: bool = False,
        visualize: bool = False,
        num_proc: int = 1,
    ) -> Union[ToolSuccess[Path], ToolError]:
        """
        Slice an stl part within a given workspace.

        Args:
            ctx: Context for long running task
            filename: Name of 3D model file to slice, should be `.stl` format.
            workspace_name: Folder name of existing workspace.
            layer_height: Optional layer height override (mm).
            hatch_spacing: Optional hatch spacing override (mm).
            build_parameters_filename: Used as the base setting for slicer.
            binary: Generate output files as binary rather than text.
            visualize: Generate visualizations of sliced layers.
            num_proc: Enable multiprocessing by specifying number of processes to use.
        """
        from wa.cli.utils import get_workspace_path

        from am.config import BuildParameters
        from am.slicer.planar import SlicerPlanar

        workspace_path = get_workspace_path(workspace_name)

        try:
            filepath = workspace_path / "parts" / filename

            build_parameters = BuildParameters.load(
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            run_name = datetime.now().strftime(f"{filepath.stem}_%Y%m%d_%H%M%S")

            # Define progress stages
            # Stage 1: Load mesh (0-10%)
            # Stage 2: Section mesh (10-20%)
            # Stage 3: Generate infill (20-70% or 20-100% if not visualizing)
            # Stage 4: Visualize infill (70-100% if visualizing)

            if visualize:
                infill_weight = 50  # 20-70%
                viz_weight = 30  # 70-100%
            else:
                infill_weight = 80  # 20-100%
                viz_weight = 0

            # Create progress callback for infill generation
            async def infill_progress_callback(current: int, total: int):
                # Map infill progress to 20-70% (or 20-100% if not visualizing)
                base_progress = 20
                progress = base_progress + int((current / total) * infill_weight)
                await ctx.report_progress(progress=progress, total=100)

            # Create progress callback for visualization
            async def viz_progress_callback(current: int, total: int):
                # Map visualization progress to 70-100%
                base_progress = 70
                progress = base_progress + int((current / total) * viz_weight)
                await ctx.report_progress(progress=progress, total=100)

            # Initialize slicer with progress callback
            slicer_planar = SlicerPlanar(
                build_parameters,
                workspace_path,
                run_name,
                progress_callback=infill_progress_callback,
            )

            # Stage 1: Load mesh
            await ctx.report_progress(progress=0, total=100)
            slicer_planar.load_mesh(filepath)
            await ctx.report_progress(progress=10, total=100)

            # Stage 2: Section mesh
            slicer_planar.section_mesh(layer_height=layer_height)
            await ctx.report_progress(progress=20, total=100)

            # Stage 3: Generate infill (with progress updates via callback)
            infill_data_out_path = await slicer_planar.generate_infill(
                hatch_spacing=hatch_spacing, binary=binary, num_proc=num_proc
            )

            if visualize:
                # Update progress callback for visualization
                slicer_planar.progress_callback = viz_progress_callback

                # Stage 4: Visualize infill (with progress updates via callback)
                visualizations_path = await slicer_planar.visualize_infill(
                    binary=binary, num_proc=num_proc
                )

                await ctx.report_progress(progress=100, total=100)
                return tool_success(visualizations_path)

            await ctx.report_progress(progress=100, total=100)
            return tool_success(infill_data_out_path)

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
