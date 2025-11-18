import sys
import typer

from rich.console import Console
from rich import print as rprint

app = typer.Typer(
    name="additive-manufacturing",
    help="Additive Manufacturing",
    add_completion=False,
    no_args_is_help=True,
)


def _rich_exception_handler(exc_type, exc_value, exc_traceback):
    """Handle exceptions with rich formatting."""
    if exc_type is KeyboardInterrupt:
        rprint("\n ⚠️  [yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    else:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.__excepthook__ = _rich_exception_handler

console = Console()
