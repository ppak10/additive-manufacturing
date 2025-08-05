from .__main__ import app
from .version import register_version

from .segmenter import segmenter_app
from .solver import solver_app
from .workspace import workspace_app
from .mcp import mcp_app

__all__ = ["app"]

app.add_typer(segmenter_app, name="segmenter")
app.add_typer(solver_app, name="solver")
app.add_typer(workspace_app, name="workspace")
app.add_typer(mcp_app, name="mcp")
_ = register_version(app)

if __name__ == "__main__":
    app()
