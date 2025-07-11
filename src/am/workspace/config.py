from pydantic import BaseModel, field_validator, model_validator
from typing import Optional
from pathlib import Path
import importlib.util
import re


class WorkspaceConfig(BaseModel):
    name: str
    out_path: Optional[Path] = None
    workspace_path: Optional[Path] = None
    verbose: Optional[bool] = False

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
