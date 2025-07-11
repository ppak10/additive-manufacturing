import typer

workspace_app = typer.Typer(
    name="workspace",
    help="Workspace management",
    add_completion=False,
    no_args_is_help=True,
)
