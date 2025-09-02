import shutil

from importlib.resources import files
from pathlib import Path
from rich import print as rprint

from am import data
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
    ):
        self.config: WorkspaceConfig = WorkspaceConfig(
            name=name, out_path=out_path, workspace_path=workspace_path
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

    def create_workspace_folders(self, workspace_path: Path):
        """
        Creates folders inputs and outputs within workspace.
        """

        # TODO: Move `mesurements` and `meshes` into a parent `runs` folder.
        folders = [
            "materials",
            "measurements",
            "meshes",
            "parts",
            "process_maps",
            "segments",
        ]
        for folder in folders:
            resource_dir = files(data) / folder
            dest_dir = workspace_path / folder
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Copies over package resources to specific folder in workspace.
            for entry in resource_dir.iterdir():
                if entry.is_file():
                    dest_file = dest_dir / entry.name
                    with entry.open("rb") as src, open(dest_file, "wb") as dst:
                        shutil.copyfileobj(src, dst)

    def create_workspace(
        self,
        out_path: Path | None = None,
        include_example_parts: bool = True,
        force: bool | None = False,
    ) -> WorkspaceConfig:
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
            raise FileExistsError("Workspace already exists")

        self.create_workspace_folders(workspace_path)

        self.config.workspace_path = workspace_path
        workspace_config_file = self.config.save()

        rprint(f"Workspace config file saved at: {workspace_config_file}")

        return self.config
