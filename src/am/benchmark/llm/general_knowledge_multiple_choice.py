import json
import re
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from .constants import DATASET_NAME, MAX_NEW_TOKENS_MULTIPLE_CHOICE


def _build_mc_prompt(row: dict) -> str:
    lines = [
        "You are an expert in additive manufacturing.",
        "Answer the following multiple-choice question by responding with only the letter of the correct answer (A, B, C, or D).",
        "",
        f"Question: {row['question']}",
        "",
        "Choices:",
    ]
    for choice in row["choices"]:
        lines.append(f"  {choice['label']}. {choice['text']}")
    lines += [
        "",
        "Answer (single letter only):",
    ]
    return "\n".join(lines)


def _parse_mc_answer(response: str) -> str | None:
    """Extract the first A/B/C/D letter from a model response."""
    match = re.search(r"\b([A-D])\b", response.strip())
    return match.group(1) if match else None


def _benchmark_general_knowledge_multiple_choice(
    runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    run_index: int = 1,
) -> dict:
    config = "general_knowledge_multiple_choice"
    print(f"\n[{config}] Loading dataset...")
    train_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]

    prompts = [_build_mc_prompt(row) for row in train_data]
    responses = runner(prompts, MAX_NEW_TOKENS_MULTIPLE_CHOICE)

    results = []
    correct_count = 0
    no_response_count = 0

    for i, row in enumerate(train_data):
        predicted = _parse_mc_answer(responses[i])
        correct = row["correct_answer"]
        is_correct = predicted == correct if predicted is not None else False
        if predicted is None:
            no_response_count += 1
        if is_correct:
            correct_count += 1

        results.append(
            {
                "source": row["source"],
                "process": row["process"],
                "question": row["question"],
                "choices": row["choices"],
                "correct_answer": correct,
                "response": responses[i],
                "predicted": predicted,
                "is_correct": is_correct,
            }
        )

    total = len(results)
    answered = total - no_response_count
    accuracy = round(correct_count / total, 4) if total else 0.0

    report = {
        "model": model,
        "dataset": DATASET_NAME,
        "config": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_questions": total,
        "no_response": no_response_count,
        "answered": answered,
        "correct": correct_count,
        "accuracy": accuracy,
        "results": results,
    }

    _print_gkmc_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_gkmc_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("General Knowledge Multiple Choice — Report")
    print(sep)
    print(f"Model:            {report['model']}")
    print(f"Total questions:  {report['total_questions']}")
    print(f"No response:      {report['no_response']}")
    print(f"Answered:         {report['answered']}")
    print(f"Correct:          {report['correct']}")
    print(f"Accuracy:         {report['accuracy']:.2%}")
    print(sep)
    for i, r in enumerate(report["results"], 1):
        mark = "✓" if r["is_correct"] else "✗"
        print(f"[{i:>3}] {mark} {r['source']} ({r['process']})")
        print(f"       Q: {r['question'][:100]}")
        print(f"       Predicted: {r['predicted']}  Correct: {r['correct_answer']}")
    print(sep)
    print(
        f"Accuracy: {report['accuracy']:.2%}  ({report['correct']}/{report['total_questions']})"
    )
    print(sep)
