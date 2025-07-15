from .__main__ import app
from .version import register_version

from .segmenter import segmenter_app
from .workspace import workspace_app

__all__ = ["app"]

app.add_typer(segmenter_app, name="segmenter")
app.add_typer(workspace_app, name="workspace")
register_version(app)

if __name__ == "__main__":
    app()
