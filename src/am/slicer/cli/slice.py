import typer


def register_slicer_slice(app: typer.Typer):
    from pathlib import Path
    from typing_extensions import Annotated

    from am.cli.options import NumProc
    from am.slicer.format import Format
    from wa.cli.options import WorkspaceOption

    @app.command(name="slice", rich_help_panel="Slicer Commands")
    def slicer_slice(
        part_filename: str,
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
        # mesh_units: str = "mm",
        build_parameters_filename: Annotated[
            str, typer.Option("--build-parameters", help="Build Parameters filename")
        ] = "default.json",
        binary: Annotated[
            bool,
            typer.Option(
                "--binary", help="Generate output files as binary rather than text."
            ),
        ] = False,
        format: Annotated[
            Format | None,
            typer.Option("--format", help="Output format for sliced geometry"),
        ] = None,
        visualize: Annotated[
            bool,
            typer.Option(
                "--visualize", help="Generate visualizations of sliced layers."
            ),
        ] = False,
        workspace_option: WorkspaceOption = None,
        num_proc: NumProc = 1,
    ) -> None:
        """
        Generates toolpath from loaded mesh (planar).
        """
        from rich import print as rprint

        from am.config import BuildParameters
        from am.slicer.models import Slicer

        from wa.cli.utils import get_workspace

        workspace = get_workspace(workspace_option)

        try:
            part_path = workspace.path / "parts" / part_filename

            build_parameters = BuildParameters.load(
                workspace.path
                / "configs"
                / "build_parameters"
                / build_parameters_filename
            )

            workspace_folder = workspace.create_folder(
                name_or_path=Path("toolpaths") / part_path.stem,
                append_timestamp=True,
            )

            import asyncio

            async def run_slicer():
                slicer = Slicer(
                    build_parameters=build_parameters, out_path=workspace_folder.path
                )

                # slicer.load_mesh(filepath, units=mesh_units)
                slicer.load_mesh(part_path)
                slicer.section_mesh(layer_height=layer_height)
                await slicer.slice_sections(
                    hatch_spacing=hatch_spacing, binary=binary, num_proc=num_proc
                )

                if format == "solver":
                    await slicer.export_solver_segments(
                        binary=binary, num_proc=num_proc
                    )

                if visualize:
                    await slicer.visualize_slices(binary=binary, num_proc=num_proc)
                slicer.save()  # Save configuration to slicer.json

            # TODO: Make workspace-agent function to update workspace.json
            # with created workspace folders.
            asyncio.run(run_slicer())

        except Exception as e:
            rprint(f"⚠️ [yellow]Unable to slice provided file: {e}[/yellow]")
            raise typer.Exit(code=1)

    return slicer_slice
