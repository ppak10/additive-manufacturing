import typer

app = typer.Typer(
    name="toolpath",
    help="Tools for generating and parsing toolpaths",
    add_completion=False,
    no_args_is_help=True,
)
