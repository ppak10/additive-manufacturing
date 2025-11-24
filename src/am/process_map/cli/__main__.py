import typer

app = typer.Typer(
    name="Process Map",
    help="Analyze combinations of build parameters and generate process maps.",
    add_completion=False,
    no_args_is_help=True,
)
