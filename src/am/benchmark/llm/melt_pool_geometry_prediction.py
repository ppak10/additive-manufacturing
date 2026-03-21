import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from datasets import load_dataset

from .constants import DATASET_NAME, MAX_NEW_TOKENS_MELT_POOL


_MELT_POOL_INPUT_FIELDS = {
    "material": "Material",
    "process": "Process",
    "power_w": "Laser Power (W)",
    "velocity_mm_s": "Scan Velocity (mm/s)",
    "beam_diameter_micron": "Beam Diameter (µm)",
    "layer_height_micron": "Layer Height (µm)",
    "hatch_spacing_micron": "Hatch Spacing (µm)",
    "melt_pool_measurement_method": "Measurement Method",
    "energy_density_j_mm_3": "Energy Density (J/mm³)",
}

_MELT_POOL_TARGETS = [
    "melt_pool_depth_micron",
    "melt_pool_width_micron",
    "melt_pool_length_micron",
]


def _build_melt_pool_prompt(row: dict) -> str:
    lines = [
        "You are an expert in additive manufacturing melt pool physics.",
        "Given the following process parameters, predict the melt pool dimensions.",
        "",
        "Parameters:",
    ]
    for key, label in _MELT_POOL_INPUT_FIELDS.items():
        val = row.get(key)
        if val is not None:
            lines.append(f"  - {label}: {val}")
    lines += [
        "",
        "Provide your predictions in the following JSON block (all values in microns):",
        "```json",
        '{"melt_pool_depth_micron": <number>, '
        '"melt_pool_width_micron": <number>, '
        '"melt_pool_length_micron": <number>}',
        "```",
    ]
    return "\n".join(lines)


def _parse_melt_pool_response(response: str) -> dict[str, float | None]:
    # Try fenced JSON block first (group 1 is the captured JSON object)
    match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: any JSON object containing the target keys (no capture group)
        match = re.search(
            r"\{[^{}]*melt_pool_depth_micron[^{}]*\}", response, re.DOTALL
        )
        json_str = match.group(0) if match else None

    if json_str:
        try:
            parsed = json.loads(json_str)

            def _to_float(v):
                if v is None:
                    return None
                if isinstance(v, (int, float)):
                    return float(v)
                if isinstance(v, str):
                    try:
                        return float(v)
                    except ValueError:
                        return None
                return None

            return {k: _to_float(parsed.get(k)) for k in _MELT_POOL_TARGETS}
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            pass

    return {k: None for k in _MELT_POOL_TARGETS}


def _rmse(pairs: list[tuple[float, float]]) -> float | None:
    if not pairs:
        return None
    valid = [
        (a, p)
        for a, p in pairs
        if not (math.isnan(a) or math.isnan(p) or math.isinf(a) or math.isinf(p))
    ]
    if not valid:
        return None
    return round(math.sqrt(sum((a - p) ** 2 for a, p in valid) / len(valid)), 4)


def _benchmark_melt_pool_geometry_prediction(
    runner,
    model: str,
    num_proc: int,
    out_path: Path | None,
    run_index: int = 1,
) -> dict:
    config = "melt_pool_geometry_prediction"
    print(f"\n[{config}] Loading dataset...")
    train_data = load_dataset(DATASET_NAME, config, num_proc=num_proc)["train"]

    prompts = [_build_melt_pool_prompt(row) for row in train_data]
    responses = runner(prompts, MAX_NEW_TOKENS_MELT_POOL)

    # Collect (actual, predicted) pairs per dimension
    dim_pairs: dict[str, list[tuple[float, float]]] = {
        k: [] for k in _MELT_POOL_TARGETS
    }
    results = []

    for i, row in enumerate(train_data):
        predicted = _parse_melt_pool_response(responses[i])
        actuals = {k: row.get(k) for k in _MELT_POOL_TARGETS}

        for dim in _MELT_POOL_TARGETS:
            if actuals[dim] is not None and predicted[dim] is not None:
                dim_pairs[dim].append((actuals[dim], predicted[dim]))

        results.append(
            {
                "doi": row.get("doi"),
                "material": row.get("material"),
                "process": row.get("process"),
                "inputs": {k: row.get(k) for k in _MELT_POOL_INPUT_FIELDS},
                "response": responses[i],
                "predicted": predicted,
                "actual": actuals,
            }
        )

    rmse_per_dim = {dim: _rmse(dim_pairs[dim]) for dim in _MELT_POOL_TARGETS}
    valid_rmse = [v for v in rmse_per_dim.values() if v is not None]
    average_rmse = round(sum(valid_rmse) / len(valid_rmse), 4) if valid_rmse else None

    report = {
        "model": model,
        "dataset": DATASET_NAME,
        "config": config,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_rows": len(results),
        "rmse": rmse_per_dim,
        "average_rmse": average_rmse,
        "results": results,
    }

    _print_mpgp_report(report)

    if out_path is not None:
        report_file = Path(out_path) / f"run_{run_index:02d}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to: {report_file}")

    return report


def _print_mpgp_report(report: dict):
    sep = "-" * 60
    print(sep)
    print("Melt Pool Geometry Prediction — Report")
    print(sep)
    print(f"Model:        {report['model']}")
    print(f"Total rows:   {report['total_rows']}")
    for dim, val in report["rmse"].items():
        label = dim.replace("melt_pool_", "").replace("_micron", "")
        print(f"RMSE {label:<8}: {val if val is not None else 'n/a'} µm")
    print(f"Average RMSE: {report['average_rmse']} µm")
    print(sep)
    for i, r in enumerate(report["results"], 1):
        print(f"[{i:>3}] {r['material']} | {r['process']}")
        pred = r["predicted"]
        actual = r["actual"]
        for dim in _MELT_POOL_TARGETS:
            label = dim.replace("melt_pool_", "").replace("_micron", "")
            p = pred[dim]
            a = actual[dim]
            print(f"       {label:<8}  pred={p}  actual={a}")
    print(sep)
    print(f"Average RMSE: {report['average_rmse']} µm")
    print(sep)
