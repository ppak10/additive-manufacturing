def _score_rubric_batch(
    nli_model,
    responses: list[str],
    rubric_data: list[list[dict]],
) -> list[tuple[float | None, list[dict]]]:
    """Score responses against rubrics using NLI entailment (label index 1).

    Returns a list of (rubric_score, details) per row.  Rows without a rubric
    get (None, []).
    """
    pairs: list[tuple[str, str]] = []
    refs: list[tuple[int, int]] = []  # (row_idx, item_idx)

    for row_idx, (response, rubric) in enumerate(zip(responses, rubric_data)):
        for item_idx, item in enumerate(rubric):
            pairs.append((response, item["concept"]))
            refs.append((row_idx, item_idx))

    if not pairs:
        return [(None, []) for _ in responses]

    scores_flat = nli_model.predict(pairs, apply_softmax=True, show_progress_bar=True)

    # Group entailment probabilities back by row
    row_entailments: list[list[tuple[int, float]]] = [[] for _ in responses]
    for (row_idx, item_idx), score_vec in zip(refs, scores_flat):
        row_entailments[row_idx].append((item_idx, float(score_vec[1])))

    output: list[tuple[float | None, list[dict]]] = []
    for row_idx, rubric in enumerate(rubric_data):
        if not rubric:
            output.append((None, []))
            continue

        details: list[dict] = []
        total = 0.0
        for item_idx, entailment_prob in sorted(row_entailments[row_idx]):
            item = rubric[item_idx]
            covered = entailment_prob > 0.5
            awarded = item["weight"] if covered else 0.0
            total += awarded
            details.append(
                {
                    "concept": item["concept"],
                    "weight": item["weight"],
                    "covered": covered,
                    "entailment_score": round(entailment_prob, 4),
                    "awarded": awarded,
                }
            )
        output.append((min(round(total, 4), 1.0), details))

    return output
