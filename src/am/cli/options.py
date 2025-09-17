import typer

from typing_extensions import Annotated

VerboseOption = Annotated[
    bool | None, typer.Option("--verbose", "-v", help="Enable verbose logging")
]
