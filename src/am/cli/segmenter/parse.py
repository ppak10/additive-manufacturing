import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated

from am.cli.options import VerboseOption
from am.segmenter import SegmenterConfig, SegmenterParse

def register_segmenter_parse(app: typer.Typer):
    @app.command(name="parse")
    def segmenter_parse(
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

        try:
            segmenter_config = SegmenterConfig.load(segmenter_config_file)
            segmenter_parse = SegmenterParse(segmenter_config)

            # Assumes file is in `workspace/segmenter/parts/`
            filepath = cwd / "segmenter" / "parts" / filename
            _ = segmenter_parse.gcode_to_commands(filepath, units)
            _ = segmenter_parse.commands_to_segments()


            filename_no_ext = filename.split(".")[0]
            segments_path = cwd / "segmenter" / "segments" / f"{filename_no_ext}.json"
            output_path = segmenter_parse.save_segments(segments_path)
            rprint(f"✅Parsed segments `{filename}` saved at `{output_path}`")
        except Exception as e:
            rprint(f"⚠️  [yellow]Unable to initialize segmenter: {e}[/yellow]")
            raise typer.Exit(code=1)

    return segmenter_parse

