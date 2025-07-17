import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption
from am.segmenter import SegmenterConfig, SegmenterGCode 

def register_segmenter_gcode(app: typer.Typer):
    @app.command(name="gcode")
    def segmenter_gcode(
        filename: str,
        units: Annotated[
            str | None, typer.Option(
                "--units",
                help="Units that the GCode is defined in."
            )
        ] = None,
        verbose: VerboseOption | None = False,
    ) -> None:
        """Create folder for segmenter data inside workspace folder."""

        # Check for workspace config file in current directory
        cwd = Path.cwd()
        workspace_config_file = cwd / "config.json"
        if not workspace_config_file.exists():
            rprint("❌ [red]This is not a valid workspace folder. `config.json` not found.[/red]")
            raise typer.Exit(code=1)

        segmenter_config_file = cwd / "segmenter" / "config.json"

        if not segmenter_config_file.exists():
            rprint("❌ [red]Segmenter not initialized. `segmenter/config.json` not found.[/red]")

        # try:
        segmenter_config = SegmenterConfig.load(segmenter_config_file)
        segmenter_gcode = SegmenterGCode(segmenter_config)

        # Assumes file is in `workspace/segmenter/parts/`
        filepath = cwd / "segmenter" / "parts" / filename
        _ = segmenter_gcode.parse_commands(filepath, units)
        _ = segmenter_gcode.commands_to_segments()


        filename_no_ext = filename.split(".")[0]
        segments_path = cwd / "segmenter" / "segments" / f"{filename_no_ext}.json"
        _ = segmenter_gcode.save_segments(segments_path)
        rprint(f"✅ GCode loaded")
        # except Exception as e:
        #     rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
        #     raise typer.Exit(code=1)

    return segmenter_gcode

