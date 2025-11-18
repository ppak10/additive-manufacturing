import typer

app = typer.Typer(
    name="slicer",
    help="Tools for slicing models and generating / parsing toolpaths",
    add_completion=False,
    no_args_is_help=True,
)
