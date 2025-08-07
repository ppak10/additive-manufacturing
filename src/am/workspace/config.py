import importlib.util
import re

from pydantic import BaseModel, field_validator, model_validator
from pathlib import Path


class WorkspaceConfig(BaseModel):
    name: str
    out_path: Path | None = None
    workspace_path: Path | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_and_sanitize_name(cls, v: str) -> str:
        v = v.replace(" ", "_")
        v = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "", v)
        return v[:255]

    @classmethod
    def get_project_root_from_package(cls) -> Path:
        """Find project root based on package installation location."""
        try:
            spec = importlib.util.find_spec("am")
            if spec and spec.origin:
                package_path = Path(spec.origin).parent
                return package_path.parent.parent
        except ImportError:
            pass
        return Path.cwd()

    @model_validator(mode="after")
    def populate_missing_paths(self) -> "WorkspaceConfig":
        if not self.out_path:
            self.out_path = self.get_project_root_from_package() / "out"

        if not self.workspace_path:
            self.workspace_path = self.out_path / self.name

        return self

    def save(self, path: Path | None = None) -> Path:
        """
        Save the configuration to a YAML file.
        If no path is given, saves to '<workspace_path>/config.yaml'.
        """
        if path is None:
            if not self.workspace_path:
                raise ValueError(
                    "workspace_path must be set to determine save location."
                )
            path = self.workspace_path / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(self.model_dump_json(indent=2))

        return path

    @classmethod
    def load(cls: type["WorkspaceConfig"], path: Path) -> "WorkspaceConfig":
        if not path.exists():
            raise FileNotFoundError(f"Config file not found at {path}")

        return cls.model_validate_json(path.read_text())
