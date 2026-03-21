import io
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from datasets import load_dataset

from .constants import MAX_NEW_TOKENS_ANOMALY_DETECTION, PEREGRINE_DATASET_NAME

_ANOMALY_LABELS = [
    "recoater_hopping",
    "recoater_streaking",
    "incomplete_spreading",
    "swelling",
    "debris",
    "super_elevation",
    "spatter",
    "misprint",
    "over_melting",
    "under_melting",
]

_DATASET_CONFIG = "anomaly_0250"
_SAMPLE_SIZE = 100
_SAMPLE_SEED = 42


def _build_anomaly_prompt() -> str:
    labels_str = "\n".join(f"- {label}" for label in _ANOMALY_LABELS)
    return (
        "You are an expert in Laser Powder Bed Fusion (L-PBF) additive manufacturing "
        "quality control and in-situ process monitoring.\n"
        "Examine this in-situ monitoring image captured after laser melting of a build layer.\n\n"
        "Identify all anomaly types present in the image from the following list:\n"
        f"{labels_str}\n\n"
        "Respond with a JSON list of the detected anomaly names. "
        "If no anomalies are detected, respond with an empty list.\n"
        'Example: ["spatter", "recoater_hopping"]\n'
        "Respond with the JSON list only, nothing else."
    )


def _parse_anomaly_response(response: str) -> list[str]:
    """Extract list of anomaly labels from model response."""
    match = re.search(r"\[.*?\]", response, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list):
                matched = []
                for item in parsed:
                    if isinstance(item, str):
                        for label in _ANOMALY_LABELS:
                            if label.lower() == item.lower().strip():
                                matched.append(label)
                                break
                return matched
        except json.JSONDecodeError:
            pass
    # Fallback: scan response for any mentioned anomaly labels
    return [
        label
        for label in _ANOMALY_LABELS
        if re.search(rf"\b{re.escape(label)}\b", response, re.IGNORECASE)
    ]


def _get_ground_truth(row: dict) -> list[str]:
    """Return list of anomaly types present in the layer (any True pixels in mask)."""
    present = []
    for label in _ANOMALY_LABELS:
        mask_bytes = row.get(f"segmentation_{label}")
        if mask_bytes is None:
            continue
        try:
            mask = np.load(io.BytesIO(bytes(mask_bytes)))
            if mask.any():
                present.append(label)
        except Exception:
            pass
    return present


def _pil_to_bytes(img) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _sample_f1(predicted: list[str], ground_truth: list[str]) -> float:
    pred_set = set(predicted)
    gt_set = set(ground_truth)
    if not pred_set and not gt_set:
        return 1.0
    if not pred_set or not gt_set:
        return 0.0
    tp = len(pred_set & gt_set)
    return round(2 * tp / (len(pred_set) + len(gt_set)), 4)


def _benchmark_peregrine_anomaly_detection(
    vision_runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    run_index: int = 1,
) -> dict:
    task = "peregrine_anomaly_detection"
    print(f"\n[{task}] Loading dataset (sampling {_SAMPLE_SIZE} of 250)...")
    full_data = load_dataset(
        PEREGRINE_DATASET_NAME,
        _DATASET_CONFIG,
        num_proc=num_proc,
    )["train"]
    data = full_data.shuffle(seed=_SAMPLE_SEED).select(range(_SAMPLE_SIZE))

    prompt_text = _build_anomaly_prompt()
    items = []
    for row in data:
        preview = row["image_after_melt_preview"]
        if hasattr(preview, "save"):  # PIL Image
            image_bytes = _pil_to_bytes(preview)
        else:
            image_bytes = bytes(preview)
        items.append(
            {
                "text": prompt_text,
                "image_bytes": image_bytes,
                "image_ext": "png",
            }
        )
    responses = vision_runner(items, MAX_NEW_TOKENS_ANOMALY_DETECTION)

    results = []
    f1_scores = []
    for i, row in enumerate(data):
        ground_truth = _get_ground_truth(row)
        predicted = _parse_anomaly_response(responses[i])
        f1 = _sample_f1(predicted, ground_truth)
        f1_scores.append(f1)
        results.append(
            {
                "build": row.get("build"),
                "layer": row.get("layer"),
                "ground_truth": ground_truth,
                "response": responses[i],
                "predicted": predicted,
                "f1": f1,
            }
        )

    total = len(results)
    mean_f1 = round(sum(f1_scores) / total, 4) if total else 0.0

    # Per-class precision, recall, F1
    per_class = {}
    for label in _ANOMALY_LABELS:
        tp = sum(
            1 for r in results if label in r["ground_truth"] and label in r["predicted"]
        )
        fp = sum(
            1
            for r in results
            if label not in r["ground_truth"] and label in r["predicted"]
        )
        fn = sum(
            1
            for r in results
            if label in r["ground_truth"] and label not in r["predicted"]
        )
        precision = round(tp / (tp + fp), 4) if (tp + fp) else 0.0
        recall = round(tp / (tp + fn), 4) if (tp + fn) else 0.0
        f1_class = (
            round(2 * precision * recall / (precision + recall), 4)
            if (precision + recall)
            else 0.0
        )
        per_class[label] = {
            "precision": precision,
            "recall": recall,
            "f1": f1_class,
            "support": tp + fn,
        }

    report = {
        "model": model,
        "dataset": PEREGRINE_DATASET_NAME,
        "config": _DATASET_CONFIG,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sample_size": _SAMPLE_SIZE,
        "total_layers": len(full_data),
        "mean_f1": mean_f1,
        "per_class": per_class,
        "results": results,
    }

    _print_peregrine_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_peregrine_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("Peregrine L-PBF Anomaly Detection — Report")
    print(sep)
    print(f"Model:        {report['model']}")
    print(f"Sample:       {report['sample_size']} / {report['total_layers']}")
    print(f"Mean F1:      {report['mean_f1']:.4f}")
    print(sep)
    print("Per-class F1:")
    for label, stats in report["per_class"].items():
        print(
            f"  {label:<25} P={stats['precision']:.2f}  R={stats['recall']:.2f}"
            f"  F1={stats['f1']:.2f}  (support={stats['support']})"
        )
    print(sep)
    for i, r in enumerate(report["results"], 1):
        gt_str = ",".join(r["ground_truth"]) or "none"
        pred_str = ",".join(r["predicted"]) or "none"
        mark = "✓" if r["f1"] == 1.0 else "~" if r["f1"] > 0 else "✗"
        print(f"[{i:>3}] {mark}  f1={r['f1']:.2f}  gt=[{gt_str}]  pred=[{pred_str}]")
    print(sep)
    print(f"Mean F1: {report['mean_f1']:.4f}")
    print(sep)
