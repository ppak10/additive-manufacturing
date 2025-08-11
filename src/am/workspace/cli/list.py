import typer

from pathlib import Path
from rich import print as rprint
from typing_extensions import Annotated
from am.cli.options import WorkspaceOption

def print_list(name: str, values: list[str] | None = None):
    rprint(f"\n  {name}:")
    if values is None:
        rprint(f"  ⚠️  [yellow]No {name} found.[/yellow]")
    else:
        for index, value in enumerate(values):
            rprint(f"  {index + 1}. [cyan]{value}[/cyan]")

def register_workspace_list(app: typer.Typer):
    @app.command(name="list")
    def workspace_list(
        meshes: Annotated[bool | None, typer.Option("--meshes", "-m", help="List meshes in workspace")] = None,
        parts: Annotated[bool | None, typer.Option("--parts", "-p", help="List parts in workspace")] = None,
        segments: Annotated[bool | None, typer.Option("--segments", "-s", help="List segments in workspace")] = None,

        all: Annotated[bool | None, typer.Option("--all", "-a", help="List all in workspace")] = None,
        workspace: WorkspaceOption = None,
    ) -> None:
        """List created workspaces."""
        if workspace is not None:
            # Get workspace path from name.
            from am.workspace import WorkspaceConfig
            project_root = WorkspaceConfig.get_project_root_from_package()
            workspace_dir = project_root / "out" / workspace

        else:
            # Check for workspace config file in current directory
            workspace_dir = Path.cwd()

        config_file = workspace_dir / "config.json"

        if not config_file.exists():
            # Default to showing available workspaces if no workspace_path.
            from am.workspace.list import list_workspaces

            try:
                workspace_names = list_workspaces()
                print_list("Workspaces", workspace_names)
            except:
                rprint("⚠️  [yellow]Unable to list workspaces[/yellow]")
                _ = typer.Exit()
        else:
            rprint(f"Workspace: {workspace}")

            if all or meshes:
                from am.workspace.list import list_workspace_meshes

                try:
                    workspace_meshes = list_workspace_meshes(workspace_dir)
                    print_list("Meshes", workspace_meshes)
                except:
                    rprint("⚠️  [yellow]Unable to list meshes[/yellow]")
                    _ = typer.Exit()

            if all or parts:
                from am.workspace.list import list_workspace_parts

                try:
                    workspace_parts = list_workspace_parts(workspace_dir)
                    print_list("Parts", workspace_parts)
                except:
                    rprint("⚠️  [yellow]Unable to list parts[/yellow]")
                    _ = typer.Exit()

            if all or segments:
                from am.workspace.list import list_workspace_segments

                try:
                    workspace_segments = list_workspace_segments(workspace_dir)
                    print_list("Segments", workspace_segments)
                except:
                    rprint("⚠️  [yellow]Unable to list segments[/yellow]")
                    _ = typer.Exit()


    _ = app.command(name="ls")(workspace_list)

    _ = (workspace_list)
