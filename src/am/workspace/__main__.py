import os

# import shutil

# from importlib.resources import files
from pathlib import Path
from rich import print as rprint

# from am import data
from am.workspace.config import WorkspaceConfig


class Workspace:
    """
    Base workspace methods.
    """

    def __init__(
        self,
        name: str,
        out_path: Path | None = None,
        workspace_path: Path | None = None,
        verbose: bool | None = False,
    ):
        self.config: WorkspaceConfig = WorkspaceConfig(
            name=name, out_path=out_path, workspace_path=workspace_path, verbose=verbose
        )

    @property
    def name(self):
        return self.config.name

    @property
    def workspace_path(self):
        return self.config.workspace_path

    @workspace_path.setter
    def workspace_path(self, value: Path):
        self.config.workspace_path = value

    @property
    def verbose(self):
        return self.config.verbose

    def create_workspace(
        self, out_path: Path | None = None, force: bool | None = False
    ):
        # Use the out_path if provided, otherwise default to package out_path.
        if out_path is None:
            out_path = self.config.out_path
            assert out_path is not None

        # Create the `out` directory if it doesn't exist.
        out_path.mkdir(exist_ok=True)

        workspace_path = out_path / self.config.name

        if workspace_path.exists() and not force:
            rprint(
                f"⚠️  [yellow]Configuration already exists at {workspace_path}[/yellow]"
            )
            rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
            raise Exception("Workspace already exists")

        self.config.workspace_path = workspace_path
        workspace_config_file = self.config.save()
        rprint(f"Workspace config file saved at: {workspace_config_file}")

        # Copy manage.py
        # resource_path = os.path.join("workspace", "manage.py")
        # manage_py_resource_path = files(data).joinpath(resource_path)
        # manage_py_workspace_path = os.path.join(self.workspace_path, "manage.py")
        # shutil.copy(manage_py_resource_path, manage_py_workspace_path)

        # Create parts directory
        # workspace_parts_path = os.path.join(self.config.workspace_path, "parts")
        # os.makedirs(workspace_parts_path, exist_ok=True)

        # resource_path = os.path.join("workspace", "parts", "README.md")
        # README_md_resource_path = files(data).joinpath(resource_path)
        # README_md_workspace_path = os.path.join(self.workspace_path, "parts", "README.md")
        # shutil.copy(README_md_resource_path, README_md_workspace_path)

        return self.config.workspace_path
