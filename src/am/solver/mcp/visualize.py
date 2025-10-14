from mcp.server import FastMCP
from pathlib import Path

from typing import Union


def register_solver_visualize(app: FastMCP):
    from am.mcp.types import ToolSuccess, ToolError
    from am.mcp.utils import tool_success, tool_error
    from am.solver.layer import SolverOutputFolder

    @app.tool(
        title="Visualize Solver",
        description="Generates the visualizations for a specific mesh that was generated and saved by a solver.",
        structured_output=True,
    )
    def solver_visualize(
        workspace: str,
        run_name: str | None = None,
        output_folder: SolverOutputFolder = SolverOutputFolder.meshes,
        frame_format: str = "png",
        include_axis: bool = True,
        transparent: bool = False,
        units: str = "mm",
    ) -> Union[ToolSuccess[Path], ToolError]:
        """Generates visualizations of mesh"""
        from wa.cli.utils import get_workspace_path

        from am.solver.layer import SolverLayer

        try:
            workspace_path = get_workspace_path(workspace)

            runs_folder = workspace_path / "meshes"
            if run_name is None:
                # Get list of subdirectories sorted by modification time (newest first)
                run_dirs = sorted(
                    [d for d in runs_folder.iterdir() if d.is_dir()],
                    key=lambda d: d.stat().st_mtime,
                    reverse=True,
                )

                if not run_dirs:
                    raise FileNotFoundError(
                        f"❌ No run directories found in {runs_folder}"
                    )

                run_name = run_dirs[0].name

            animation_out_path = SolverLayer.visualize_2D(
                workspace_path,
                run_name,
                output_folder,
                frame_format=frame_format,
                include_axis=include_axis,
                transparent=transparent,
                units=units,
            )

            return tool_success(animation_out_path)

        except PermissionError as e:
            return tool_error(
                "Permission denied when visualizing solver mesh",
                "PERMISSION_DENIED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
            )

        except Exception as e:
            return tool_error(
                "Failed to visualize solver mesh",
                "SOLVER_MESH_VISUALIZE_FAILED",
                workspace_name=workspace,
                exception_type=type(e).__name__,
                exception_message=str(e),
            )

    _ = solver_visualize
