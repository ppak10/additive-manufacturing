from .__main__ import app

# from .version import register_version

from am.config.cli import app as config_app
from am.mcp.cli import app as mcp_app
from am.slicer.cli.slice import register_slicer_slice
from am.simulator.cli import app as simulator_app
from am.workspace.cli import app as workspace_app

__all__ = ["app"]

app.add_typer(config_app, name="config")
app.add_typer(mcp_app, name="mcp")
app.add_typer(simulator_app, name="simulator")
app.add_typer(workspace_app, name="workspace")

_ = register_slicer_slice(app)
# _ = register_version(app)

if __name__ == "__main__":
    app()
