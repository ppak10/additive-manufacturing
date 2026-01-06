import typer

app = typer.Typer(
    name="simulator",
    help="Run simulations such as toolpath based residual heat and process mapping.",
    add_completion=False,
    no_args_is_help=True,
)

