import typer

app = typer.Typer(
    name="segmenter",
    help="Segmenter management",
    add_completion=False,
    no_args_is_help=True,
)
