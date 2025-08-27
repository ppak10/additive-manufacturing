import typer

app = typer.Typer(
    name="schema",
    help="Create schema used within package methods",
    add_completion=False,
    no_args_is_help=True,
)

