import typer

from typing_extensions import Annotated

from wa.cli.options import WorkspaceOption



def register_toolpath_generate(app: typer.Typer):
    from am.config.build_parameters import DEFAULT

    @app.command(name="generate")
    def toolpath_generate(
        filename: str,

        # TODO: Move to its own CLI method of generate_nonplanar
        # nonplanar: Annotated[bool, typer.Option("--nonplanar")] = False,

        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build Parameters filename")
        ] = "default.json",

        workspace: WorkspaceOption = None,
    ) -> None:
        """
        Generates toolpath from loaded mesh (planar).
        """
        from rich import print as rprint

        from am.config import BuildParameters
        from am.toolpath import ToolpathSlicerPlanar

        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            filepath = workspace_path / "parts" / filename

            build_parameters = BuildParameters.load(
                workspace_path / "build_parameters" / build_parameters_filename
            )

            toolpath_slicer_planar = ToolpathSlicerPlanar()
            toolpath_slicer_planar.load_mesh(filepath)
            toolpath_slicer_planar.slice(build_parameters, workspace_path)

        except Exception as e:
            rprint(f"⚠️ [yellow]Unable to slice provided file: {e}[/yellow]")
            raise typer.Exit(code=1)

    return toolpath_generate

