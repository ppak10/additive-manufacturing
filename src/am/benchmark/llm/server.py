import json
import os
import signal
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from contextlib import contextmanager


def _has_chat_template(model_id: str) -> bool:
    """Return True if the HF tokenizer config contains a chat_template field."""
    try:
        from huggingface_hub import hf_hub_download

        path = hf_hub_download(model_id, "tokenizer_config.json")
        with open(path) as f:
            cfg = json.load(f)
        return bool(cfg.get("chat_template"))
    except Exception:
        return True  # assume it has one if we can't check


def _get_it_model_template(model_id: str) -> str | None:
    """Try to fetch the chat template from the corresponding IT/instruct variant.

    Many base (pretrained) models follow the naming convention:
      …-pt  →  …-it   (e.g. gemma-3-12b-pt → gemma-3-12b-it)
      …-base → …-instruct

    Returns the Jinja2 template string if found, else None.
    """
    candidates = []
    if model_id.endswith("-pt"):
        candidates.append(model_id[:-3] + "-it")
    if "-base" in model_id:
        candidates.append(model_id.replace("-base", "-instruct"))

    for candidate in candidates:
        try:
            from huggingface_hub import hf_hub_download

            path = hf_hub_download(candidate, "tokenizer_config.json")
            with open(path) as f:
                cfg = json.load(f)
            template = cfg.get("chat_template")
            if template:
                print(f"[server] Borrowed chat template from IT model: {candidate}")
                return template if isinstance(template, str) else json.dumps(template)
        except Exception:
            continue
    return None


def _write_template_file(template: str) -> str:
    """Write a Jinja2 template string to a temp file and return its path."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".jinja", delete=False, prefix="am_chat_template_"
    )
    tmp.write(template)
    tmp.close()
    return tmp.name


# Minimal text-only fallback template (no image support).
_TEXT_ONLY_CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "{{ message['content'] if message['content'] is string else "
    "(message['content'] | selectattr('type', 'equalto', 'text') | map(attribute='text') | join(' ')) }}"
    "{% if not loop.last %}\n{% endif %}"
    "{% endfor %}"
)


def _is_model_cached(model_id: str) -> bool:
    """Return True if the model is already present in the local HF cache."""
    try:
        from huggingface_hub import scan_cache_dir

        cache_info = scan_cache_dir()
        for repo in cache_info.repos:
            if repo.repo_id == model_id:
                return True
        return False
    except Exception:
        return False


def _is_lora_adapter(model_id: str) -> bool:
    try:
        from huggingface_hub import hf_hub_download

        hf_hub_download(model_id, "adapter_config.json")
        return True
    except Exception:
        return False


def _get_lora_base_model(model_id: str) -> str:
    import json
    from huggingface_hub import hf_hub_download

    path = hf_hub_download(model_id, "adapter_config.json")
    with open(path) as f:
        config = json.load(f)
    return config["base_model_name_or_path"]


def _get_free_gpu_index() -> int:
    """Returns the lowest-indexed GPU with more than half its VRAM free."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,memory.free,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        rows = []
        for line in result.stdout.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 3:
                rows.append((int(parts[0]), int(parts[1]), int(parts[2])))
        rows.sort(key=lambda r: r[0])
        for idx, free, total in rows:
            if total > 0 and free > total * 0.5:
                return idx
    except Exception:
        pass
    return 0


def _kill_port(port: int) -> None:
    """Kill any process currently listening on the given TCP port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"],
            capture_output=True,
            text=True,
        )
        pids = [int(p) for p in result.stdout.strip().splitlines() if p.strip()]
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        if pids:
            time.sleep(2)
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            print(
                f"[server] Cleaned up {len(pids)} leftover process(es) on port {port}."
            )
    except Exception:
        pass


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Send SIGTERM then SIGKILL to the entire process group."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    except ProcessLookupError:
        pass


def _wait_for_server(url: str, timeout: int = 300) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/models", timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(3)
    return False


@contextmanager
def managed_vllm_server(
    model_id: str,
    port: int = 8000,
    extra_args: list[str] | None = None,
    cuda_visible_devices: str | None = None,
    label: str = "server",
):
    is_lora = _is_lora_adapter(model_id)
    tmp_template_path = None

    if is_lora:
        base_model = _get_lora_base_model(model_id)
        print(f"[{label}] Detected LoRA adapter. Base model: {base_model}")

    # Use a longer startup timeout when the model isn't cached locally,
    # since vLLM will need to download it first.
    model_to_check = base_model if is_lora else model_id
    cached = _is_model_cached(model_to_check)
    startup_timeout = 300 if cached else 3600
    if not cached:
        print(
            f"[{label}] Model '{model_to_check}' not found in local cache. "
            f"Startup timeout extended to {startup_timeout}s to allow for download."
        )

    if is_lora:
        cmd = [
            "vllm",
            "serve",
            base_model,
            "--port",
            str(port),
            "--enable-lora",
            "--lora-modules",
            f"{model_id}={model_id}",
        ]
    else:
        cmd = ["vllm", "serve", model_id, "--port", str(port)]
        if not _has_chat_template(model_id):
            # Try to borrow the chat template from the corresponding IT model.
            # This is the most reliable path for base models (e.g. gemma-3-12b-pt
            # borrows from gemma-3-12b-it) because it includes the correct image
            # placeholder tokens already known to work with that model family.
            it_template = _get_it_model_template(model_id)
            if it_template:
                print(
                    f"[{label}] No chat template in {model_id}; "
                    "using borrowed IT model template."
                )
                tmp_template_path = _write_template_file(it_template)
            else:
                print(
                    f"[{label}] No chat template found for {model_id}. "
                    "Injecting a text-only default chat template."
                )
                tmp_template_path = _write_template_file(_TEXT_ONLY_CHAT_TEMPLATE)
            cmd.extend(["--chat-template", tmp_template_path])

    if extra_args:
        cmd.extend(extra_args)

    # Always pin to a single GPU; auto-pick the one with the most free VRAM
    # if the caller didn't specify one explicitly.
    if cuda_visible_devices is None:
        cuda_visible_devices = str(_get_free_gpu_index())
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = cuda_visible_devices

    server_url = f"http://localhost:{port}/v1"
    _kill_port(port)
    print(f"[{label}] Starting vLLM on GPU {cuda_visible_devices}: {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, env=env, start_new_session=True)
    try:
        if not _wait_for_server(server_url, timeout=startup_timeout):
            _kill_process_group(proc)
            raise RuntimeError(
                f"vLLM server did not become ready within {startup_timeout}s on port {port}"
            )
        print(f"[{label}] vLLM server ready.")
        yield server_url, model_id
    finally:
        _kill_process_group(proc)
        _kill_port(port)
        print(f"[{label}] vLLM server stopped.")
        if tmp_template_path:
            try:
                os.unlink(tmp_template_path)
            except Exception:
                pass
