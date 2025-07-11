from .__main__ import app, workspace_app, VerboseOption

from .workspace_initialize import register_workspace_initialize
from .version import register_version

__all__ = ["app", "VerboseOption"]

register_workspace_initialize(workspace_app)

app.add_typer(workspace_app, name="workspace")
register_version(app)

if __name__ == "__main__":
    app()

