import typer

app = typer.Typer(
    name="config",
    help="Create configuration files used within package methods.",
    add_completion=False,
    no_args_is_help=True,
)
