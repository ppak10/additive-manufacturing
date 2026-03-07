import importlib
from pathlib import Path

from .constants import TASKS
from .inference import _run_openai_compatible, _run_transformers
from .general_knowledge_multiple_choice import (
    _benchmark_general_knowledge_multiple_choice,
)
from .general_knowledge_short_answer import _benchmark_general_knowledge_short_answer
from .melt_pool_geometry_prediction import _benchmark_melt_pool_geometry_prediction


def benchmark_llm(
    model: str,
    tasks: list[str] = TASKS,
    num_proc: int = 1,
    batch_size: int = 8,
    url: str | None = None,
    out_path: Path | None = None,
) -> dict:

    missing = [
        pkg
        for pkg in ("datasets", "sentence_transformers", "transformers")
        if importlib.util.find_spec(pkg) is None
    ]
    if missing:
        raise ImportError(
            f"Missing benchmark packages: {', '.join(missing)}. "
            'Run: uv pip install "additive-manufacturing[benchmark]"'
        )

    if url is not None:
        print(f"Using vLLM server: {url}")
        runner = lambda questions, max_tokens: _run_openai_compatible(
            url, model, questions, max_tokens
        )
    else:
        from transformers import pipeline

        print(f"Loading model: {model}")
        llm_pipeline = pipeline(
            "text-generation",
            model=model,
            return_full_text=False,
            device_map="auto",
        )
        runner = lambda questions, max_tokens: _run_transformers(
            llm_pipeline, questions, batch_size, max_tokens
        )

    reports = {}
    for task in tasks:
        if task == "general_knowledge_multiple_choice":
            reports[task] = _benchmark_general_knowledge_multiple_choice(
                runner, model, num_proc, out_path
            )
        elif task == "general_knowledge_short_answer":
            reports[task] = _benchmark_general_knowledge_short_answer(
                runner, model, num_proc, out_path
            )
        elif task == "melt_pool_geometry_prediction":
            reports[task] = _benchmark_melt_pool_geometry_prediction(
                runner, model, num_proc, out_path
            )
        else:
            print(f"Unknown task '{task}', skipping.")

    return reports
