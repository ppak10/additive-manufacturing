import typer

from typing_extensions import Annotated

from am.cli.options import VerboseOption, WorkspaceOption

def register_segmenter_parse(app: typer.Typer):
    @app.command(name="parse")
    def segmenter_parse(
        filename: str,
        distance_xy_max: Annotated[float, typer.Option("--distance-xy-max")] = 1.0,
        units: Annotated[str, typer.Option("--units")] = "mm",
        workspace: WorkspaceOption = None,
        verbose: VerboseOption = False,
    ) -> None:
        """
        Parses `.gcode` file within workspace parts folder into segments.
        """
        import asyncio
        asyncio.run(_segmenter_parse_async(filename, distance_xy_max, units, workspace, verbose))

    return segmenter_parse


async def _segmenter_parse_async(
    filename: str,
    distance_xy_max: float,
    units: str,
    workspace: WorkspaceOption = None,
    verbose: VerboseOption = False,
) -> None:
    from pathlib import Path
    from rich import print as rprint
    from am.segmenter import SegmenterParse

    if workspace is not None:
        from am.workspace import WorkspaceConfig
        project_root = WorkspaceConfig.get_project_root_from_package()
        workspace_dir = project_root / "out" / workspace
    else:
        workspace_dir = Path.cwd()

    workspace_config_file = workspace_dir / "config.json"
    if not workspace_config_file.exists():
        rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
        raise typer.Exit(code=1)

    try:
        segmenter_parse = SegmenterParse()
        filepath = workspace_dir / "parts" / filename

        await segmenter_parse.gcode_to_commands(filepath, units, verbose=verbose)
        await segmenter_parse.commands_to_segments(distance_xy_max=distance_xy_max, units=units, verbose=verbose)

        filename_no_ext = filename.split(".")[0]
        segments_path = workspace_dir / "segments" / f"{filename_no_ext}.json"
        output_path = segmenter_parse.save_segments(segments_path, verbose=verbose)
        rprint(f"✅Parsed segments `{filename}` saved at `{output_path}`")
    except Exception as e:
        rprint(f"⚠️  [yellow]Unable to segment {filename}: {e}[/yellow]")
        raise typer.Exit(code=1)


