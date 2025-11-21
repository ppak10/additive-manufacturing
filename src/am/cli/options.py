import typer

from typing_extensions import Annotated

VerboseOption = Annotated[
    bool | None, typer.Option("--verbose", "-v", help="Enable verbose logging")
]

NumProc = Annotated[
    int,
    typer.Option(
        "--num-proc",
        help="Enable multiprocessing by specifying number of processes to use.",
    ),
]
