import typer

from typing_extensions import Annotated

VerboseOption = Annotated[
    bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
]
