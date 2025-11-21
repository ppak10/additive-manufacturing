import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated


def register_process_map_create(app: typer.Typer):
    @app.command(name="create")
    def process_map_create(
        process_map_folder_name: str,
        build_parameters_file_name: str,
        material_file_name: str,
        process_map_file_name: str,
        workspace_name: str,
        workspaces_path: Path | None = None,
        force: Annotated[
            bool, typer.Option("--force", help="Overwrite existing subfolder")
        ] = False,
    ) -> None:
        """
        Creates a process map folder with configs for build parameter, material,
        and process map.
        """

        from am.process_map.create import create_process_map_folder
        from am.config import BuildParameters, Material, ProcessMap

        from wa.cli.utils import get_workspace_path

        try:
            workspace_path = get_workspace_path(workspace_name)

            build_parameters = BuildParameters.load(
                workspace_path
                / "configs"
                / "build_parameters"
                / build_parameters_file_name
            )
            material = Material.load(
                workspace_path / "configs" / "materials" / material_file_name
            )
            process_map = ProcessMap.load(
                workspace_path / "configs" / "process_maps" / process_map_file_name
            )

            process_map_folder = create_process_map_folder(
                process_map_folder_name=process_map_folder_name,
                build_parameters=build_parameters,
                material=material,
                process_map=process_map,
                workspace_name=workspace_name,
                workspaces_path=workspaces_path,
                force=force,
            )

            rprint(f"✅ Process Map folder created at: {process_map_folder.path}")
        except FileExistsError as e:
            rprint(
                f"⚠️  [yellow]Workspace: `{process_map_folder_name}` already exists.[/yellow]"
            )
            rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
            _ = typer.Exit()
        except:
            rprint("⚠️  [yellow]Unable to create process map directory[/yellow]")
            _ = typer.Exit()

    return process_map_create
