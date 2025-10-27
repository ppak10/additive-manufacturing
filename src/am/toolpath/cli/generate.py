import typer

from typing_extensions import Annotated

from wa.cli.options import WorkspaceOption

def register_toolpath_generate(app: typer.Typer):
    @app.command(name="generate")
    def toolpath_generate(
        filename: str,
        nonplanar: Annotated[bool, typer.Option("--nonplanar")] = False,
        workspace: WorkspaceOption = None,
    ) -> None:
        """
        Generates toolpath from loaded mesh.
        """
        from rich import print as rprint

        from am.toolpath import ToolpathSlicerPlanar
        from wa.cli.utils import get_workspace_path

        workspace_path = get_workspace_path(workspace)

        try:
            filepath = workspace_path / "parts" / filename

            if not nonplanar:
                toolpath_slicer_planar = ToolpathSlicerPlanar()
                toolpath_slicer_planar.load_mesh(filepath)
            else:
                raise NotImplemented 

        except Exception as e:
            rprint(f"⚠️ [yellow]Unable to slice provided file: {e}[/yellow]")
            raise typer.Exit(code=1)

    return toolpath_generate

