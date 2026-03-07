import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm


def _run_openai_compatible(
    url: str, model: str, questions: list[str], max_tokens: int
) -> list[str]:
    def _request(index: int, question: str) -> tuple[int, str]:
        payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": question}],
                "max_tokens": max_tokens,
            }
        ).encode()
        req = urllib.request.Request(
            f"{url}/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            print(f"\n[warning] Request {index} failed with HTTP {e.code}: {e.reason}")
            return index, ""
        if "choices" not in data:
            print(
                f"\n[warning] Request {index} returned no choices: {data.get('error', data)}"
            )
            return index, ""
        content = data["choices"][0]["message"]["content"]
        return index, content.strip() if content is not None else ""

    responses = [""] * len(questions)
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_request, i, q): i for i, q in enumerate(questions)}
        for future in tqdm(
            as_completed(futures), total=len(questions), desc="LLM inference"
        ):
            i, content = future.result()
            responses[i] = content
    return responses


def _run_transformers(
    pipeline, questions: list[str], batch_size: int, max_tokens: int
) -> list[str]:
    from transformers import GenerationConfig

    generation_config = GenerationConfig(max_new_tokens=max_tokens)
    responses = []
    for i in tqdm(range(0, len(questions), batch_size), desc="LLM inference"):
        batch = questions[i : i + batch_size]
        outputs = pipeline(batch, generation_config=generation_config)
        responses.extend(o[0]["generated_text"].strip() for o in outputs)
    return responses
