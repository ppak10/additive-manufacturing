import typer

app = typer.Typer(
    name="workspace",
    help="Workspace management for `additive-manufacturing` package.",
    add_completion=False,
    no_args_is_help=True,
)
