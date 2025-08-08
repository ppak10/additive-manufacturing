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

    @classmethod
    def list_workspaces(cls, out_path: Path | None = None) -> list[str] | None:
        """
        Lists workspace directories within out_path
        """
        if out_path is None:
            project_root = WorkspaceConfig.get_project_root_from_package()
            out_path = project_root / "out"

        if not out_path.exists() or not out_path.is_dir():
            return None

        return [
            workspace_dir.name
            for workspace_dir in out_path.iterdir()
            if workspace_dir.is_dir()
        ]

    @classmethod
    def list_workspace_parts(
            cls,
            workspace: str,
            out_path: Path | None = None,
            suffix: str = ".gcode",
    ) -> list[str] | None:
        """
        Lists workspace directories within out_path
        """
        if out_path is None:
            project_root = WorkspaceConfig.get_project_root_from_package()
            out_path = project_root / "out"

        if not out_path.exists() or not out_path.is_dir():
            return None

        parts_path = out_path / workspace / "parts"

        return [
            partfile.name
            for partfile in parts_path.iterdir()
            if partfile.is_file() and partfile.suffix == suffix
        ]


    def copy_example_parts(self, path: Path):
        parts_resource_dir = files(data) / "parts"
        parts_dest_dir = path / "parts"
        parts_dest_dir.mkdir(parents=True, exist_ok=True)

        for entry in parts_resource_dir.iterdir():
            if entry.is_file():
                dest_file = parts_dest_dir / entry.name
                with entry.open("rb") as src, open(dest_file, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        rprint(f"Copied example part files to: {parts_dest_dir}")

    def create_workspace(
        self,
        out_path: Path | None = None,
        include_example_parts: bool = True,
        force: bool | None = False
    ) -> WorkspaceConfig:
        # Use the out_path if provided, otherwise default to package out_path.
        if out_path is None:
            out_path = self.config.out_path
            assert out_path is not None

        # Create the `out` directory if it doesn't exist.
        out_path.mkdir(exist_ok=True)

        workspace_path = out_path / self.config.name

        print(workspace_path)

        if workspace_path.exists() and not force:
            rprint(
                f"⚠️  [yellow]Configuration already exists at {workspace_path}[/yellow]"
            )
            rprint("Use [cyan]--force[/cyan] to overwrite, or edit the existing file.")
            raise FileExistsError("Workspace already exists")

        if include_example_parts:
            self.copy_example_parts(workspace_path)

        self.config.workspace_path = workspace_path
        workspace_config_file = self.config.save()

        rprint(f"Workspace config file saved at: {workspace_config_file}")

        return self.config


