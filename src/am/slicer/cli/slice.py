import typer

from datetime import datetime
from typing_extensions import Annotated

from wa.cli.options import WorkspaceOption


def register_slicer_slice(app: typer.Typer):

    @app.command(name="slice")
    def slicer_slice(
        filename: str,
        layer_height: Annotated[
            float | None,
            typer.Option("--layer-height", help="Optional layer height override (mm)."),
        ] = None,
        hatch_spacing: Annotated[
            float | None,
            typer.Option(
                "--hatch_spacing", help="Optional hatch spacing override (mm)."
            ),
        ] = None,
        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build Parameters filename")
        ] = "default.json",
        binary: Annotated[
            bool,
            typer.Option(
                "--binary", help="Generate output files as binary rather than text."
            ),
        ] = False,
        visualize: Annotated[
            bool,
            typer.Option(
                "--visualize", help="Generate visualizations of sliced layers."
            ),
        ] = False,
        workspace: WorkspaceOption = None,
        num_proc: Annotated[
            int,
            typer.Option(
                "--num-proc",
                help="Enable multiprocessing by specifying number of processes to use.",
            ),
        ] = 1,
    ) -> None:
        """
        Generates toolpath from loaded mesh (planar).
        """
        from rich import print as rprint

        from am.config import BuildParameters
        from am.slicer.planar import SlicerPlanar

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            filepath = workspace_path / "parts" / filename

            build_parameters = BuildParameters.load(
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            run_name = datetime.now().strftime(f"{filepath.stem}_%Y%m%d_%H%M%S")

            import asyncio

            async def run_slicer():
                slicer_planar = SlicerPlanar(build_parameters, workspace_path, run_name)

                slicer_planar.load_mesh(filepath)
                slicer_planar.section_mesh(layer_height=layer_height)
                await slicer_planar.generate_infill(
                    hatch_spacing=hatch_spacing, binary=binary, num_proc=num_proc
                )

                if visualize:
                    await slicer_planar.visualize_infill(
                        binary=binary, num_proc=num_proc
                    )

            asyncio.run(run_slicer())

        except Exception as e:
            rprint(f"⚠️ [yellow]Unable to slice provided file: {e}[/yellow]")
            raise typer.Exit(code=1)

    return slicer_slice
