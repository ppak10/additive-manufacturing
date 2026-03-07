import typer


def register_benchmark(app: typer.Typer):
    from pathlib import Path
    from rich import print as rprint

    from am.benchmark.llm import benchmark_llm, TASKS
    from am.cli.options import NumProc
    from wa.cli.options import WorkspaceOption

    @app.command(name="benchmark", rich_help_panel="Benchmark Commands")
    def benchmark(
        model: str,
        tasks: list[str] = typer.Option(TASKS, help="Tasks to benchmark"),
        batch_size: int = typer.Option(
            8, help="Number of prompts to process in parallel."
        ),
        url: str = typer.Option(
            None, help="URL of a running vLLM server (e.g. http://localhost:8000/v1)."
        ),
        workspace_option: WorkspaceOption = None,
        num_proc: NumProc = 1,
    ) -> None:
        """
        Runs additive manufacturing benchmark for large language models.
        """

        from wa.cli.utils import get_workspace

        workspace = get_workspace(workspace_option)

        try:
            workspace_folder_path = None
            if workspace:
                model_name = model.replace("/", "--")
                workspace_folder = workspace.create_folder(
                    name_or_path=Path("benchmarks") / model_name, append_timestamp=True
                )
                workspace_folder_path = workspace_folder.path

            benchmark_llm(
                model=model,
                tasks=tasks,
                batch_size=batch_size,
                url=url,
                num_proc=num_proc,
                out_path=workspace_folder_path,
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            rprint(f"⚠️ [yellow]Unable to run benchmark for {model}: {e}[/yellow]")
            raise typer.Exit(code=1)

    return benchmark
