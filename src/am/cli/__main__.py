import sys
import typer

from typing_extensions import Annotated

from rich.console import Console
from rich import print as rprint

app = typer.Typer(
    name="additive-manufacturing",
    help="Additive Manufacturing Tools",
    add_completion=False,
    no_args_is_help=True,
)

workspace_app = typer.Typer(
    name="workspace",
    help="Workspace management",
    add_completion=False,
    no_args_is_help=True,
)

VerboseOption = Annotated[
    bool, typer.Option("--verbose", "-v", help="Enable verbose logging")
]


def _rich_exception_handler(exc_type, exc_value, exc_traceback):
    """Handle exceptions with rich formatting."""
    if exc_type is KeyboardInterrupt:
        rprint("\n ⚠️  [yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.__excepthook__ = _rich_exception_handler

console = Console()
