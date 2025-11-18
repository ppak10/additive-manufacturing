import typer

from typing_extensions import Annotated


def register_mcp_uninstall(app: typer.Typer):
    @app.command(name="uninstall")
    def mcp_uninstall(
        client: Annotated[
            str, typer.Argument(help="Target client to uninstall.")
        ] = "claude-code",
    ) -> None:
        from am.mcp.uninstall import uninstall

        uninstall(client=client)

    _ = app.command(name="uninstall")(mcp_uninstall)
    return mcp_uninstall
