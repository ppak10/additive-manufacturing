import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption, WorkspaceOption

def register_segmenter_parse(app: typer.Typer):
    @app.command(name="parse")
    def segmenter_parse(
        filename: str,
        distance_xy_max: Annotated[float, typer.Option("--distance-xy-max")] = 1.0,
        units: Annotated[str, typer.Option("--units")] = "mm",
        workspace: WorkspaceOption | None = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        import asyncio
        asyncio.run(_segmenter_parse_async(filename, distance_xy_max, units, workspace, verbose))

    return segmenter_parse


async def _segmenter_parse_async(
    filename: str,
    distance_xy_max: float,
    units: str,
    workspace: WorkspaceOption | None,
    verbose: VerboseOption | None,
) -> None:
    from pathlib import Path
    from rich import print as rprint
    from am.segmenter import SegmenterConfig, SegmenterParse

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

    segmenter_config_file = workspace_dir / "segmenter" / "config.json"
    if not segmenter_config_file.exists():
        rprint("❌ [red]Segmenter not initialized. `segmenter/config.json` not found.[/red]")

    try:
        segmenter_config = SegmenterConfig.load(segmenter_config_file)
        segmenter_parse = SegmenterParse(segmenter_config)
        filepath = workspace_dir / "segmenter" / "parts" / filename

        await segmenter_parse.gcode_to_commands(filepath, units, verbose=verbose)
        await segmenter_parse.commands_to_segments(distance_xy_max=distance_xy_max, units=units, verbose=verbose)

        filename_no_ext = filename.split(".")[0]
        segments_path = workspace_dir / "segmenter" / "segments" / f"{filename_no_ext}.json"
        output_path = segmenter_parse.save_segments(segments_path, verbose=verbose)
        rprint(f"✅Parsed segments `{filename}` saved at `{output_path}`")
    except Exception as e:
        rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
        raise typer.Exit(code=1)


# def register_segmenter_parse(app: typer.Typer):
#     @app.command(name="parse")
#     async def segmenter_parse(
#         filename: str,
#         distance_xy_max: Annotated[
#             float,
#             typer.Option(
#                 "--distance-xy-max", help="Maximum xy distance for a single segment."
#             ),
#         ] = 1.0,
#         units: Annotated[
#             str, typer.Option("--units", help="Units that the GCode is defined in.")
#         ] = "mm",
#         workspace: WorkspaceOption | None = None,
#         verbose: VerboseOption | None = False,
#     ) -> None:
#         """Create folder for segmenter data inside workspace folder."""
#         from am.segmenter import SegmenterConfig, SegmenterParse
#
#         # Check for workspace config file in current directory
#         if workspace is not None:
#             # Get workspace path from name.
#             from am.workspace import WorkspaceConfig
#             project_root = WorkspaceConfig.get_project_root_from_package()
#             workspace_dir = project_root / "out" / workspace
#
#         else:
#             # Check for workspace config file in current directory
#             workspace_dir = Path.cwd()
#
#         workspace_config_file = workspace_dir / "config.json"
#         if not workspace_config_file.exists():
#             rprint(
#                 "❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]"
#             )
#             raise typer.Exit(code=1)
#
#         segmenter_config_file = workspace_dir / "segmenter" / "config.json"
#
#         if not segmenter_config_file.exists():
#             rprint(
#                 "❌ [red]Segmenter not initialized. `segmenter/config.json` not found.[/red]"
#             )
#
#         try:
#             segmenter_config = SegmenterConfig.load(segmenter_config_file)
#             segmenter_parse = SegmenterParse(segmenter_config)
#
#             # Assumes file is in `workspace/segmenter/parts/`
#             filepath = workspace_dir / "segmenter" / "parts" / filename
#
#             await segmenter_parse.gcode_to_commands(filepath, units, verbose=verbose)
#             await segmenter_parse.commands_to_segments(
#                 distance_xy_max=distance_xy_max, units=units, verbose=verbose
#             )
#
#             filename_no_ext = filename.split(".")[0]
#             segments_path = workspace_dir / "segmenter" / "segments" / f"{filename_no_ext}.json"
#             output_path = segmenter_parse.save_segments(segments_path, verbose=verbose)
#             rprint(f"✅Parsed segments `{filename}` saved at `{output_path}`")
#         except Exception as e:
#             rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
#             raise typer.Exit(code=1)
#
#     return segmenter_parse

