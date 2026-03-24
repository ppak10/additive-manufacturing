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
        proctor_url: str = typer.Option(
            None,
            help="URL of vLLM server for rubric proctoring (e.g. http://localhost:8001/v1).",
        ),
        proctor_model: str = typer.Option(
            "openai/gpt-oss-20b", help="Model name for rubric proctoring."
        ),
        port: int = typer.Option(
            8000, help="Local port for the auto-started vLLM server."
        ),
        num_runs: int = typer.Option(
            1, help="Number of benchmark runs (for error bar statistics)."
        ),
        vllm_args: list[str] = typer.Option(
            [],
            "--vllm-arg",
            help="Extra argument forwarded to 'vllm serve' (repeatable, e.g. --vllm-arg='--max-model-len=8192').",
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
                port=port,
                num_runs=num_runs,
                num_proc=num_proc,
                out_path=workspace_folder_path,
                proctor_url=proctor_url,
                proctor_model=proctor_model,
                vllm_extra_args=vllm_args or None,
            )

        except Exception as e:
            import traceback

            traceback.print_exc()
            rprint(f"⚠️ [yellow]Unable to run benchmark for {model}: {e}[/yellow]")
            raise typer.Exit(code=1)

    return benchmark
