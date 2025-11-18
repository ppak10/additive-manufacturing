import typer

app = typer.Typer(
    name="solver",
    help="Solver management",
    add_completion=False,
    no_args_is_help=True,
)
