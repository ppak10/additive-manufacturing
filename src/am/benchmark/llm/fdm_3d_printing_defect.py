import json
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from .constants import DATASET_NAME, MAX_NEW_TOKENS_DEFECT_CLASSIFICATION

_DEFECT_LABELS = ["Cracking", "Layer_shifting", "Off_platform", "Stringing", "Warping"]
_SAMPLE_SIZE = 100
_SAMPLE_SEED = 42


def _build_defect_prompt() -> str:
    labels_str = "\n".join(f"- {label}" for label in _DEFECT_LABELS)
    return (
        "You are an expert in additive manufacturing quality control.\n"
        "Look at this image of a 3D printed part and classify the defect shown.\n\n"
        f"Choose exactly one of the following defect types:\n{labels_str}\n\n"
        "Respond with only the defect type name, nothing else."
    )


def _parse_defect_response(response: str) -> str | None:
    for label in _DEFECT_LABELS:
        if label.lower() in response.lower():
            return label
    return None


def _benchmark_fdm_3d_printing_defect(
    vision_runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    run_index: int = 1,
) -> dict:
    config = "fdm_3d_printing_defect"
    print(f"\n[{config}] Loading dataset (sampling {_SAMPLE_SIZE} of 1912)...")
    full_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]
    data = full_data.shuffle(seed=_SAMPLE_SEED).select(range(_SAMPLE_SIZE))

    prompt_text = _build_defect_prompt()
    items = [
        {
            "text": prompt_text,
            "image_bytes": row["image"],
            "image_ext": row["image_ext"],
        }
        for row in data
    ]
    responses = vision_runner(items, MAX_NEW_TOKENS_DEFECT_CLASSIFICATION)

    results = []
    correct_count = 0
    no_response_count = 0

    for i, row in enumerate(data):
        predicted = _parse_defect_response(responses[i])
        label = row["label"]
        is_correct = predicted == label if predicted is not None else False
        if predicted is None:
            no_response_count += 1
        if is_correct:
            correct_count += 1

        results.append(
            {
                "filename": row["filename"],
                "label": label,
                "response": responses[i],
                "predicted": predicted,
                "is_correct": is_correct,
            }
        )

    total = len(results)
    accuracy = round(correct_count / total, 4) if total else 0.0

    report = {
        "model": model,
        "dataset": DATASET_NAME,
        "config": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_size": _SAMPLE_SIZE,
        "total_images": len(full_data),
        "no_response": no_response_count,
        "correct": correct_count,
        "accuracy": accuracy,
        "results": results,
    }

    _print_fdm_defect_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_fdm_defect_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("FDM 3D Printing Defect Classification — Report")
    print(sep)
    print(f"Model:         {report['model']}")
    print(f"Sample:        {report['sample_size']} / {report['total_images']}")
    print(f"No response:   {report['no_response']}")
    print(f"Correct:       {report['correct']}")
    print(f"Accuracy:      {report['accuracy']:.2%}")
    print(sep)
    for i, r in enumerate(report["results"], 1):
        mark = "✓" if r["is_correct"] else "✗"
        print(f"[{i:>3}] {mark}  label={r['label']:<16} predicted={r['predicted']}")
    print(sep)
    print(
        f"Accuracy: {report['accuracy']:.2%}  ({report['correct']}/{report['sample_size']})"
    )
    print(sep)
