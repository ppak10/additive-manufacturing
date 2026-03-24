import importlib
from pathlib import Path

from .constants import PROCTOR_MODEL, TASKS
from .inference import _run_openai_compatible, _run_openai_compatible_vision
from .general_knowledge_multiple_choice import (
    _benchmark_general_knowledge_multiple_choice,
)
from .general_knowledge_short_answer import _benchmark_general_knowledge_short_answer
from .melt_pool_geometry_prediction import _benchmark_melt_pool_geometry_prediction
from .fdm_3d_printing_defect import _benchmark_fdm_3d_printing_defect
from .machines import _benchmark_machines
from .peregrine_anomaly_detection import _benchmark_peregrine_anomaly_detection
from .score_card import _compile_score_card


def _run_benchmark_tasks(
    runner,
    vision_runner,
    model,
    tasks,
    num_proc,
    out_path,
    proctor_url,
    proctor_model,
    run_index: int = 1,
) -> dict:
    reports = {}
    for task in tasks:
        task_out = None
        if out_path is not None:
            task_out = Path(out_path) / task
            task_out.mkdir(parents=True, exist_ok=True)

        if task == "general_knowledge_multiple_choice":
            reports[task] = _benchmark_general_knowledge_multiple_choice(
                runner, model, num_proc, task_out, run_index=run_index
            )
        elif task == "general_knowledge_short_answer":
            reports[task] = _benchmark_general_knowledge_short_answer(
                runner,
                model,
                num_proc,
                task_out,
                proctor_url=proctor_url,
                proctor_model=proctor_model,
                run_index=run_index,
            )
        elif task == "melt_pool_geometry_prediction":
            reports[task] = _benchmark_melt_pool_geometry_prediction(
                runner, model, num_proc, task_out, run_index=run_index
            )
        elif task == "fdm_3d_printing_defect":
            reports[task] = _benchmark_fdm_3d_printing_defect(
                vision_runner, model, num_proc, task_out, run_index=run_index
            )
        elif task == "machines":
            reports[task] = _benchmark_machines(
                vision_runner,
                model,
                num_proc,
                task_out,
                proctor_url=proctor_url,
                proctor_model=proctor_model,
                run_index=run_index,
            )
        elif task == "peregrine_anomaly_detection":
            reports[task] = _benchmark_peregrine_anomaly_detection(
                vision_runner, model, num_proc, task_out, run_index=run_index
            )
        else:
            print(f"Unknown task '{task}', skipping.")

    return reports


def benchmark_llm(
    model: str,
    tasks: list[str] = TASKS,
    num_proc: int = 1,
    batch_size: int = 8,
    url: str | None = None,
    port: int = 8000,
    num_runs: int = 1,
    out_path: Path | None = None,
    proctor_url: str | None = None,
    proctor_model: str = PROCTOR_MODEL,
    vllm_extra_args: list[str] | None = None,
) -> list[dict]:

    missing = [pkg for pkg in ("datasets",) if importlib.util.find_spec(pkg) is None]
    if missing:
        raise ImportError(
            f"Missing benchmark packages: {', '.join(missing)}. "
            'Run: uv pip install "additive-manufacturing[benchmark]"'
        )

    needs_auto_proctor = proctor_url is None and (
        "general_knowledge_short_answer" in tasks or "machines" in tasks
    )

    def _do_runs(runner, vision_runner, serve_model, actual_proctor_url):
        all_reports = []
        for run_idx in range(1, num_runs + 1):
            if num_runs > 1:
                print(f"\n=== Run {run_idx}/{num_runs} ===")
            reports = _run_benchmark_tasks(
                runner,
                vision_runner,
                serve_model,
                tasks,
                num_proc,
                out_path,
                actual_proctor_url,
                proctor_model,
                run_index=run_idx,
            )
            all_reports.append(reports)
        _compile_score_card(serve_model, all_reports, out_path, num_runs=num_runs)
        return all_reports

    def _with_proctor(runner, vision_runner, serve_model):
        if needs_auto_proctor:
            from .server import managed_vllm_server

            proctor_port = port + 1
            print(
                f"[proctor] Auto-starting proctor '{proctor_model}' on port {proctor_port}..."
            )
            with managed_vllm_server(
                proctor_model,
                port=proctor_port,
                label="proctor",
            ) as (p_url, _):
                return _do_runs(runner, vision_runner, serve_model, p_url)
        else:
            return _do_runs(runner, vision_runner, serve_model, proctor_url)

    if url is not None:
        print(f"Using vLLM server: {url}")
        runner = lambda questions, max_tokens: _run_openai_compatible(
            url, model, questions, max_tokens
        )
        vision_runner = lambda items, max_tokens: _run_openai_compatible_vision(
            url, model, items, max_tokens
        )
        return _with_proctor(runner, vision_runner, model)
    else:
        from .server import managed_vllm_server

        with managed_vllm_server(model, port=port, extra_args=vllm_extra_args) as (
            server_url,
            serve_model,
        ):
            runner = lambda questions, max_tokens: _run_openai_compatible(
                server_url, serve_model, questions, max_tokens
            )
            vision_runner = lambda items, max_tokens: _run_openai_compatible_vision(
                server_url, serve_model, items, max_tokens
            )
            return _with_proctor(runner, vision_runner, serve_model)
