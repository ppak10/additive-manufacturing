import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import NumProc


def register_process_map_run(app: typer.Typer):
    @app.command(name="run")
    def process_map_run(
        process_map_folder_name: str,
        workspace_name: str,
        # workspaces_path: Path | None = None,
        num_proc: NumProc = 1,
    ) -> None:
        """
        Runs process map with build parameter, material, and process map config.
        """

        from am.process_map.run import run_process_map
        from am.config import BuildParameters, Material, ProcessMap

        from wa.cli.utils import get_workspace_path

        # try:
        workspace_path = get_workspace_path(workspace_name)

        process_map_path = workspace_path / "process_maps" / process_map_folder_name

        build_parameters = BuildParameters.load(
            process_map_path / "config" / "build_parameters.json"
        )
        material = Material.load(process_map_path / "config" / "material.json")
        process_map = ProcessMap.load(process_map_path / "config" / "process_map.json")

        run_process_map(
            build_parameters=build_parameters,
            material=material,
            process_map=process_map,
            process_map_path=process_map_path,
            num_proc=num_proc,
        )

        # except FileExistsError as e:
        #     rprint(f"⚠️  [yellow]Process Map: `{process_map_folder_name}` already exists.[/yellow]")
        #     rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
        #     _ = typer.Exit()
        # except:
        #     rprint("⚠️  [yellow]Unable to run process map[/yellow]")
        #     _ = typer.Exit()

    return process_map_run
