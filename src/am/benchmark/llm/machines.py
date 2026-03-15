import json
import random
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

_SAMPLE_PER_CATEGORY = 10
_SAMPLE_SEED = 42

from .constants import (
    DATASET_NAME,
    MAX_NEW_TOKENS_MACHINES,
    MAX_NEW_TOKENS_PROCTOR,
    PROCTOR_MODEL,
)
from .rubric import _score_machines_batch_llm


def _build_machines_prompt() -> str:
    return (
        "You are an expert in additive manufacturing equipment.\n"
        "Look at this image of an additive manufacturing machine.\n\n"
        "Identify the following:\n"
        "1. Manufacturing process type (e.g., FDM, SLA, PBF, DED, binder jet, etc.)\n"
        "2. Machine name / model\n"
        "3. Manufacturer\n\n"
        "Respond with valid JSON only, no explanation:\n"
        '{"process": "<process_type>", "name": "<machine_name>", "manufacturer": "<manufacturer>"}'
    )


def _benchmark_machines(
    vision_runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    proctor_url: str | None = None,
    proctor_model: str = PROCTOR_MODEL,
    run_index: int = 1,
) -> dict:
    config = "machines"
    print(
        f"\n[{config}] Loading dataset (sampling up to {_SAMPLE_PER_CATEGORY} per category)..."
    )
    full_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]

    # Stratified sample: up to _SAMPLE_PER_CATEGORY per process category
    rng = random.Random(_SAMPLE_SEED)
    by_process: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(full_data):
        by_process[row["process"]].append(i)
    selected_indices = []
    for process, indices in sorted(by_process.items()):
        selected_indices.extend(
            rng.sample(indices, min(_SAMPLE_PER_CATEGORY, len(indices)))
        )
    selected_indices.sort()
    data = full_data.select(selected_indices)

    prompt_text = _build_machines_prompt()
    items = [
        {
            "text": prompt_text,
            "image_bytes": row["image"],
            "image_ext": row["image_ext"],
        }
        for row in data
    ]
    responses = vision_runner(items, MAX_NEW_TOKENS_MACHINES)

    ground_truth = [{"process": row["process"], "name": row["name"]} for row in data]

    scores_and_details: list[tuple[float, dict]] = [(0.0, {})] * len(responses)
    if proctor_url is None:
        print(f"[{config}] Warning: --proctor-url not set. Skipping proctor scoring.")
    else:
        print(
            f"[{config}] Scoring responses via LLM judge ({proctor_model} @ {proctor_url})..."
        )
        scores_and_details = _score_machines_batch_llm(
            url=proctor_url,
            proctor_model=proctor_model,
            responses=responses,
            ground_truth=ground_truth,
            max_tokens=MAX_NEW_TOKENS_PROCTOR,
        )

    results = []
    for i, row in enumerate(data):
        score, details = scores_and_details[i]
        results.append(
            {
                "name": row["name"],
                "process": row["process"],
                "response": responses[i],
                "score": score,
                "details": details,
            }
        )

    total = len(results)
    scored = [r for r in results if r["details"]]
    total_score = round(sum(r["score"] for r in scored), 4) if scored else None
    max_score = len(scored)
    avg_score = (
        round(total_score / max_score, 4)
        if total_score is not None and max_score
        else None
    )

    field_accuracy = None
    if scored:
        field_accuracy = {
            "process": round(
                sum(r["details"].get("process_correct", False) for r in scored)
                / len(scored),
                4,
            ),
            "name": round(
                sum(r["details"].get("name_correct", False) for r in scored)
                / len(scored),
                4,
            ),
            "manufacturer": round(
                sum(r["details"].get("manufacturer_correct", False) for r in scored)
                / len(scored),
                4,
            ),
        }

    report = {
        "model": model,
        "dataset": DATASET_NAME,
        "config": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_per_category": _SAMPLE_PER_CATEGORY,
        "total_machines": len(full_data),
        "sample_size": total,
        "total_score": total_score,
        "max_score": max_score,
        "avg_score": avg_score,
        "field_accuracy": field_accuracy,
        "results": results,
    }

    _print_machines_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_machines_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("Machines Identification — Report")
    print(sep)
    print(f"Model:       {report['model']}")
    print(
        f"Sample:      {report['sample_size']} / {report['total_machines']} (up to {report['sample_per_category']} per category)"
    )
    if report.get("total_score") is not None:
        print(f"Score:       {report['total_score']:.4f} / {report['max_score']}")
        print(f"Avg score:   {report['avg_score']:.4f}")
    if report.get("field_accuracy"):
        fa = report["field_accuracy"]
        print(f"  Process (×0.50): {fa['process']:.2%}")
        print(f"  Name    (×0.25): {fa['name']:.2%}")
        print(f"  Mfr     (×0.25): {fa['manufacturer']:.2%}")
    print(sep)
    for i, r in enumerate(report["results"], 1):
        details = r.get("details") or {}
        p = "✓" if details.get("process_correct") else "✗"
        n = "✓" if details.get("name_correct") else "✗"
        m = "✓" if details.get("manufacturer_correct") else "✗"
        score_str = f"{r['score']:.2f}" if r.get("score") is not None else "n/a"
        print(
            f"[{i:>3}] score={score_str}  proc={p} name={n} mfr={m}  gt={r['name']} ({r['process']})"
        )
    print(sep)
    if report.get("avg_score") is not None:
        print(f"Avg score: {report['avg_score']:.4f}")
    print(sep)
