from .__main__ import app
from .version import register_version

from am.segmenter.cli import app as segmenter_app
from am.solver.cli import app as solver_app
from am.workspace.cli import app as workspace_app
from am.mcp.cli import app as mcp_app

__all__ = ["app"]

app.add_typer(segmenter_app, name="segmenter")
app.add_typer(solver_app, name="solver")
app.add_typer(workspace_app, name="workspace")
app.add_typer(mcp_app, name="mcp")
_ = register_version(app)

if __name__ == "__main__":
    app()

