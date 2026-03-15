import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from .constants import (
    DATASET_NAME,
    MAX_NEW_TOKENS_SHORT_ANSWER,
    MAX_NEW_TOKENS_PROCTOR,
    PROCTOR_MODEL,
)
from .rubric import _score_rubric_batch_llm


def _benchmark_general_knowledge_short_answer(
    runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    proctor_url: str | None = None,
    proctor_model: str = PROCTOR_MODEL,
    run_index: int = 1,
) -> dict:
    config = "general_knowledge_short_answer"
    print(f"\n[{config}] Loading dataset...")
    train_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]

    questions = [row["question"] for row in train_data]
    responses = runner(questions, MAX_NEW_TOKENS_SHORT_ANSWER)

    # Parse rubric column (may be a JSON string or already a list)
    rubric_data: list[list[dict]] = []
    for row in train_data:
        raw = row.get("rubric")
        if raw is None:
            rubric_data.append([])
        elif isinstance(raw, str):
            try:
                rubric_data.append(json.loads(raw))
            except json.JSONDecodeError:
                rubric_data.append([])
        else:
            rubric_data.append(raw)

    rubric_scores_and_details: list[tuple[float | None, list[dict]]] = [
        (None, []) for _ in responses
    ]
    if any(rubric_data):
        if proctor_url is None:
            print(
                f"[{config}] Warning: rubric data found but --proctor-url not set. "
                "Skipping rubric scoring."
            )
        else:
            print(
                f"[{config}] Scoring rubric concepts via LLM judge "
                f"({proctor_model} @ {proctor_url})..."
            )
            rubric_scores_and_details = _score_rubric_batch_llm(
                url=proctor_url,
                proctor_model=proctor_model,
                questions=questions,
                responses=responses,
                rubric_data=rubric_data,
                max_tokens=MAX_NEW_TOKENS_PROCTOR,
            )

    results = []
    for i, row in enumerate(train_data):
        rubric_score, rubric_details = rubric_scores_and_details[i]
        results.append(
            {
                "source": row["source"],
                "process": row["process"],
                "question": row["question"],
                "response": responses[i],
                "rubric_score": rubric_score,
                "rubric_details": rubric_details,
            }
        )

    valid_rubric = [r["rubric_score"] for r in results if r["rubric_score"] is not None]
    total_rubric_score = round(sum(valid_rubric), 4) if valid_rubric else None
    max_rubric_score = len(valid_rubric)
    no_response_count = sum(1 for r in results if not r["response"])

    report = {
        "model": model,
        "dataset": DATASET_NAME,
        "config": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_questions": len(results),
        "no_response": no_response_count,
        "total_rubric_score": total_rubric_score,
        "max_rubric_score": max_rubric_score,
        "results": results,
    }

    _print_gksa_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_gksa_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("General Knowledge Short Answer — Report")
    print(sep)
    print(f"Model:            {report['model']}")
    print(f"Total questions:  {report['total_questions']}")
    print(f"No response:      {report.get('no_response', 0)}")
    if report.get("total_rubric_score") is not None:
        print(
            f"Rubric score:     {report['total_rubric_score']} / {report['max_rubric_score']}"
        )
    print(sep)
    for i, r in enumerate(report["results"], 1):
        print(f"[{i:>3}] {r['source']} ({r['process']})")
        print(f"       Q: {r['question']}")
        print(f"       A: {r['response'][:120]}")
        rubric_str = (
            f"rubric={r['rubric_score']}"
            if r.get("rubric_score") is not None
            else "rubric=N/A"
        )
        print(f"       Scores: {rubric_str}")
    print(sep)
    if report.get("total_rubric_score") is not None:
        print(
            f"Rubric score:  {report['total_rubric_score']} / {report['max_rubric_score']}"
        )
    print(sep)
