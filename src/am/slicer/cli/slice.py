import typer

from datetime import datetime
from typing_extensions import Annotated

from wa.cli.options import WorkspaceOption


def register_slicer_slice(app: typer.Typer):
    from am.config.build_parameters import DEFAULT

    @app.command(name="slice")
    def slicer_slice(
        filename: str,
        # TODO: Move to its own CLI method of generate_nonplanar
        # nonplanar: Annotated[bool, typer.Option("--nonplanar")] = False,
        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build Parameters filename")
        ] = "default.json",
        workspace: WorkspaceOption = None,
        num_proc: Annotated[int, typer.Option("--num-proc")] = 1,
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

            slicer_planar = SlicerPlanar(build_parameters, workspace_path, run_name)

            slicer_planar.load_mesh(filepath)
            slicer_planar.section_mesh()
            slicer_planar.generate_infill(num_proc=num_proc)
            slicer_planar.visualize_infill(num_proc=num_proc)

        except Exception as e:
            rprint(f"⚠️ [yellow]Unable to slice provided file: {e}[/yellow]")
            raise typer.Exit(code=1)

    return slicer_slice
