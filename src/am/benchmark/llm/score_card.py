import json
import statistics
from datetime import datetime, timezone
from pathlib import Path


def _stats(values: list, num_runs: int):
    """Return mean for a single run, or {"mean": ..., "std": ...} for multiple runs."""
    valid = [v for v in values if v is not None]
    if not valid:
        return None
    mean = round(statistics.mean(valid), 4)
    if num_runs > 1:
        std = round(statistics.stdev(valid), 4) if len(valid) > 1 else 0.0
        return {"mean": mean, "std": std, "runs": valid}
    return mean


def _compile_score_card(
    model: str,
    all_reports: list[dict],
    out_path: Path | None,
    num_runs: int = 1,
) -> dict:
    tasks_summary = {}

    def _gather(task, key):
        return [r[task].get(key) for r in all_reports if task in r]

    if any("general_knowledge_multiple_choice" in r for r in all_reports):
        tasks_summary["general_knowledge_multiple_choice"] = {
            "accuracy": _stats(
                _gather("general_knowledge_multiple_choice", "accuracy"), num_runs
            ),
            "correct": _stats(
                _gather("general_knowledge_multiple_choice", "correct"), num_runs
            ),
            "total_questions": all_reports[0]["general_knowledge_multiple_choice"].get(
                "total_questions"
            ),
        }

    if any("general_knowledge_short_answer" in r for r in all_reports):
        tasks_summary["general_knowledge_short_answer"] = {
            "total_rubric_score": _stats(
                _gather("general_knowledge_short_answer", "total_rubric_score"),
                num_runs,
            ),
            "max_rubric_score": all_reports[0]["general_knowledge_short_answer"].get(
                "max_rubric_score"
            ),
            "total_questions": all_reports[0]["general_knowledge_short_answer"].get(
                "total_questions"
            ),
        }

    if any("melt_pool_geometry_prediction" in r for r in all_reports):
        tasks_summary["melt_pool_geometry_prediction"] = {
            "average_rmse_micron": _stats(
                _gather("melt_pool_geometry_prediction", "average_rmse"), num_runs
            ),
            "rmse": {
                dim: _stats(
                    [
                        r["melt_pool_geometry_prediction"]["rmse"].get(dim)
                        for r in all_reports
                        if "melt_pool_geometry_prediction" in r
                    ],
                    num_runs,
                )
                for dim in [
                    "melt_pool_depth_micron",
                    "melt_pool_width_micron",
                    "melt_pool_length_micron",
                ]
            },
            "total_rows": all_reports[0]["melt_pool_geometry_prediction"].get(
                "total_rows"
            ),
        }

    if any("fdm_3d_printing_defect" in r for r in all_reports):
        tasks_summary["fdm_3d_printing_defect"] = {
            "accuracy": _stats(_gather("fdm_3d_printing_defect", "accuracy"), num_runs),
            "correct": _stats(_gather("fdm_3d_printing_defect", "correct"), num_runs),
            "sample_size": all_reports[0]["fdm_3d_printing_defect"].get("sample_size"),
            "total_images": all_reports[0]["fdm_3d_printing_defect"].get(
                "total_images"
            ),
        }

    if any("machines" in r for r in all_reports):
        tasks_summary["machines"] = {
            "total_score": _stats(_gather("machines", "total_score"), num_runs),
            "max_score": all_reports[0]["machines"].get("max_score"),
            "avg_score": _stats(_gather("machines", "avg_score"), num_runs),
            "field_accuracy": {
                field: _stats(
                    [
                        r["machines"]["field_accuracy"].get(field)
                        for r in all_reports
                        if "machines" in r and r["machines"].get("field_accuracy")
                    ],
                    num_runs,
                )
                for field in ["process", "name", "manufacturer"]
            },
            "sample_size": all_reports[0]["machines"].get("sample_size"),
        }

    dataset = next((r[next(iter(r))].get("dataset") for r in all_reports if r), None)
    score_card = {
        "model": model,
        "dataset": dataset,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_runs": num_runs,
        "tasks": tasks_summary,
    }

    if out_path is not None:
        score_card_file = Path(out_path) / "score_card.json"
        with open(score_card_file, "w") as f:
            json.dump(score_card, f, indent=2)
        print(f"\nScore card saved to: {score_card_file}")

    return score_card
