import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from .constants import (
    DATASET_NAME,
    EVALUATOR_MODEL,
    RUBRIC_EVALUATOR_MODEL,
    MAX_NEW_TOKENS_SHORT_ANSWER,
)
from .rubric import _score_rubric_batch


def _benchmark_general_knowledge_short_answer(
    runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
) -> dict:
    from sentence_transformers import SentenceTransformer
    from sentence_transformers.util import cos_sim

    config = "general_knowledge_short_answer"
    print(f"\n[{config}] Loading dataset...")
    train_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]

    print(f"[{config}] Loading evaluator: {EVALUATOR_MODEL}")
    evaluator = SentenceTransformer(EVALUATOR_MODEL, device="cuda:1")

    answer_solutions = [row.get("answer_solution") or "" for row in train_data]
    answer_submissions = [row.get("answer_submission") or "" for row in train_data]

    print(f"[{config}] Pre-computing answer embeddings...")
    sol_embs = evaluator.encode(
        answer_solutions, convert_to_tensor=True, show_progress_bar=True
    )
    sub_embs = evaluator.encode(
        answer_submissions, convert_to_tensor=True, show_progress_bar=True
    )

    questions = [row["question"] for row in train_data]
    responses = runner(questions, MAX_NEW_TOKENS_SHORT_ANSWER)

    print(f"[{config}] Encoding responses...")
    response_embs = evaluator.encode(
        responses, convert_to_tensor=True, show_progress_bar=True
    )

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

    rubric_scores_and_details: list[tuple[float | None, list[dict]]] = []
    if any(rubric_data):
        from sentence_transformers import CrossEncoder

        print(f"[{config}] Loading rubric evaluator: {RUBRIC_EVALUATOR_MODEL}")
        nli_model = CrossEncoder(RUBRIC_EVALUATOR_MODEL, device="cuda:1")
        print(f"[{config}] Scoring rubric concepts...")
        rubric_scores_and_details = _score_rubric_batch(
            nli_model, responses, rubric_data
        )
    else:
        rubric_scores_and_details = [(None, []) for _ in responses]

    results = []
    for i, row in enumerate(train_data):
        scores = {}
        if answer_solutions[i]:
            scores["answer_solution"] = round(
                float(cos_sim(response_embs[i], sol_embs[i])), 4
            )
        if answer_submissions[i]:
            scores["answer_submission"] = round(
                float(cos_sim(response_embs[i], sub_embs[i])), 4
            )

        best_score = max(scores.values()) if scores else None
        rubric_score, rubric_details = rubric_scores_and_details[i]
        results.append(
            {
                "source": row["source"],
                "process": row["process"],
                "question": row["question"],
                "response": responses[i],
                "scores": scores,
                "best_score": best_score,
                "rubric_score": rubric_score,
                "rubric_details": rubric_details,
            }
        )

    valid_scores = [r["best_score"] for r in results if r["best_score"] is not None]
    average_score = (
        round(sum(valid_scores) / len(valid_scores), 4) if valid_scores else 0.0
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
        "evaluated": len(valid_scores),
        "average_score": average_score,
        "total_rubric_score": total_rubric_score,
        "max_rubric_score": max_rubric_score,
        "results": results,
    }

    _print_gksa_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"{config}.json"
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
    print(f"Evaluated:        {report['evaluated']}")
    print(f"Average score:    {report['average_score']}")
    if report.get("total_rubric_score") is not None:
        print(
            f"Rubric score:     {report['total_rubric_score']} / {report['max_rubric_score']}"
        )
    print(sep)
    for i, r in enumerate(report["results"], 1):
        print(f"[{i:>3}] {r['source']} ({r['process']})")
        print(f"       Q: {r['question']}")
        print(f"       A: {r['response'][:120]}")
        scores_str = "  ".join(f"{k}={v}" for k, v in r["scores"].items())
        rubric_str = (
            f"  rubric={r['rubric_score']}" if r.get("rubric_score") is not None else ""
        )
        print(f"       Scores: {scores_str}  =>  best={r['best_score']}{rubric_str}")
    print(sep)
    print(f"Average score: {report['average_score']}")
    if report.get("total_rubric_score") is not None:
        print(
            f"Rubric score:  {report['total_rubric_score']} / {report['max_rubric_score']}"
        )
    print(sep)
