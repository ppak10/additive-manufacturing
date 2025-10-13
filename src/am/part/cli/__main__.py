import typer

app = typer.Typer(
    name="part",
    help="Part management",
    add_completion=False,
    no_args_is_help=True,
)
