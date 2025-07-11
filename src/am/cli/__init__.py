from .__main__ import app, VerboseOption
from .version import register_version

from .workspace.__main__ import workspace_app
from .workspace.initialize import register_workspace_initialize

__all__ = ["app", "VerboseOption"]

register_workspace_initialize(workspace_app)

app.add_typer(workspace_app, name="workspace")
register_version(app)

if __name__ == "__main__":
    app()
