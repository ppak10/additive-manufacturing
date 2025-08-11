import typer

from pathlib import Path
from rich import print as rprint

from am.cli.options import WorkspaceOption

def get_workspace_path(workspace: WorkspaceOption) -> Path:
    """
    Checks for workspace config file in current directory or throws error.
    """
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
        rprint(
            f"❌ [red]This is not a valid workspace folder. `{config_file}` not found.[/red]"
        )
        raise typer.Exit(code=1)

    return workspace_dir

