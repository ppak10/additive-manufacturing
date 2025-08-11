import typer

from typing_extensions import Annotated

VerboseOption = Annotated[
    bool | None, typer.Option("--verbose", "-v", help="Enable verbose logging")
]

WorkspaceOption = Annotated[
    str | None, typer.Option("--workspace", "-w", help="Workspace to perform operation")
]

