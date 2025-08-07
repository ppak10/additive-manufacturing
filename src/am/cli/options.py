import typer

from typing_extensions import Annotated

VerboseOption = Annotated[
    bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
]

WorkspaceOption = Annotated[
    str, typer.Option("--workspace", "-w", help="Workspace to perform operation")
]
