import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


def _score_rubric_batch_llm(
    url: str,
    proctor_model: str,
    questions: list[str],
    responses: list[str],
    rubric_data: list[list[dict]],
    max_tokens: int = 512,
) -> list[tuple[float | None, list[dict]]]:
    """Score responses against rubric concepts using an LLM judge.

    Returns a list of (rubric_score, details) per row.  Rows without a rubric
    get (None, []).
    """

    def _score_one(idx: int) -> tuple[int, float | None, list[dict]]:
        rubric = rubric_data[idx]
        if not rubric:
            return idx, None, []

        question = questions[idx]
        response = responses[idx]

        concept_lines = "\n".join(
            f"{i + 1}. {item['concept']}" for i, item in enumerate(rubric)
        )
        prompt = (
            "You are an expert evaluator for additive manufacturing knowledge.\n\n"
            "Evaluate whether the following response covers each rubric concept.\n\n"
            f"Question: {question}\n\n"
            f"Response: {response}\n\n"
            f"Rubric concepts:\n{concept_lines}\n\n"
            "For each concept, determine if the response covers it (true) or not (false).\n"
            'Respond with valid JSON only, no explanation:\n{"covered": [true_or_false, ...]}'
        )

        payload = json.dumps(
            {
                "model": proctor_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0,
            }
        ).encode()
        req = urllib.request.Request(
            f"{url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        raw = ""
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                raw = content.strip() if content is not None else ""
            else:
                print(
                    f"\n[warning] Rubric request {idx} returned no choices: "
                    f"{data.get('error', data)}"
                )
        except urllib.error.HTTPError as e:
            print(
                f"\n[warning] Rubric request {idx} failed with HTTP {e.code}: {e.reason}"
            )

        # Robust JSON parsing: find first {...} block
        covered: list[bool] = [False] * len(rubric)
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                raw_covered = parsed.get("covered", [])
                for i, val in enumerate(raw_covered):
                    if i < len(covered):
                        covered[i] = bool(val)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass  # fall back to all False

        details: list[dict] = []
        total = 0.0
        for i, item in enumerate(rubric):
            is_covered = covered[i] if i < len(covered) else False
            awarded = item["weight"] if is_covered else 0.0
            total += awarded
            details.append(
                {
                    "concept": item["concept"],
                    "weight": item["weight"],
                    "covered": is_covered,
                    "awarded": awarded,
                }
            )
        return idx, min(round(total, 4), 1.0), details

    n = len(responses)
    output: list[tuple[float | None, list[dict]]] = [(None, [])] * n

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_score_one, i): i for i in range(n)}
        for future in as_completed(futures):
            idx, score, details = future.result()
            output[idx] = (score, details)

    return output


_MACHINES_WEIGHTS = {"process": 0.5, "name": 0.25, "manufacturer": 0.25}


def _score_machines_batch_llm(
    url: str,
    proctor_model: str,
    responses: list[str],
    ground_truth: list[dict],
    max_tokens: int = 256,
) -> list[tuple[float, dict]]:
    """Score machines task responses via LLM judge.

    ground_truth items: {'process': str, 'name': str}
    Returns list of (score, details) where details has process_correct,
    name_correct, manufacturer_correct keys.
    """

    def _score_one(idx: int) -> tuple[int, float, dict]:
        gt = ground_truth[idx]
        response = responses[idx]

        prompt = (
            "You are evaluating an AI model's ability to identify an additive manufacturing machine from an image.\n\n"
            f"Ground truth:\n"
            f"- Process: {gt['process']}\n"
            f"- Machine identifier (name + manufacturer): {gt['name']}\n\n"
            f"Model response: {response}\n\n"
            "Determine whether the model correctly identified:\n"
            f"1. process_correct: Does the model's process match \"{gt['process']}\"? "
            "(Allow abbreviations/expansions, e.g. 'Fused Deposition Modeling' for 'FDM'.)\n"
            f"2. name_correct: Does the model's machine name match \"{gt['name']}\"? "
            "(Allow minor spacing/punctuation differences.)\n"
            f"3. manufacturer_correct: Does the model's manufacturer match the manufacturer "
            f"implied by \"{gt['name']}\"?\n\n"
            "Respond with valid JSON only, no explanation:\n"
            '{"process_correct": true_or_false, "name_correct": true_or_false, "manufacturer_correct": true_or_false}'
        )

        payload = json.dumps(
            {
                "model": proctor_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0,
            }
        ).encode()
        req = urllib.request.Request(
            f"{url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )

        raw = ""
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                raw = content.strip() if content is not None else ""
            else:
                print(
                    f"\n[warning] Machines rubric request {idx} returned no choices: "
                    f"{data.get('error', data)}"
                )
        except urllib.error.HTTPError as e:
            print(
                f"\n[warning] Machines rubric request {idx} failed with HTTP {e.code}: {e.reason}"
            )

        details = {
            "process_correct": False,
            "name_correct": False,
            "manufacturer_correct": False,
        }
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                for key in details:
                    if key in parsed:
                        details[key] = bool(parsed[key])
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        score = round(
            _MACHINES_WEIGHTS["process"] * details["process_correct"]
            + _MACHINES_WEIGHTS["name"] * details["name_correct"]
            + _MACHINES_WEIGHTS["manufacturer"] * details["manufacturer_correct"],
            4,
        )
        return idx, score, details

    n = len(responses)
    output: list[tuple[float, dict]] = [(0.0, {})] * n

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_score_one, i): i for i in range(n)}
        for future in as_completed(futures):
            idx, score, details = future.result()
            output[idx] = (score, details)

    return output
