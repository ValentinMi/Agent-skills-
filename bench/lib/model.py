"""Local-model client for the benchmark kit — Ollama chat API, stdlib only.

Two entry points:
- chat(): one system+user turn against a local model (Ollama /api/chat).
- judge(): ask an evaluator model a YES/NO criterion, get {passed, evidence}.

A "mock" model short-circuits the HTTP call so the whole pipeline
(runner -> grading -> aggregate) can be exercised without a real backend.
In mock mode chat() returns the eval's `mock_response` and judge() passes
everything — it proves plumbing, it does not fake real scores.
"""

import json
import os
import re
import time
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
DEFAULT_MODEL = os.environ.get("BENCH_MODEL", "qwen2.5-coder:7b")
DEFAULT_TIMEOUT = int(os.environ.get("BENCH_TIMEOUT", "300"))


def is_mock(model: str) -> bool:
    return model == "mock" or os.environ.get("BENCH_MOCK") == "1"


def _post(url: str, payload: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(
    system: str,
    user: str,
    model: str = DEFAULT_MODEL,
    url: str = DEFAULT_URL,
    temperature: float = 0.0,
    timeout: int = DEFAULT_TIMEOUT,
    mock_response: str = "",
) -> dict:
    """Run one system+user turn. Returns {content, seconds, error}."""
    if is_mock(model):
        return {"content": mock_response, "seconds": 0.0, "error": None}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": temperature},
    }
    start = time.time()
    try:
        body = _post(url, payload, timeout)
        content = body.get("message", {}).get("content", "")
        return {"content": content, "seconds": time.time() - start, "error": None}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"content": "", "seconds": time.time() - start, "error": str(e)}


_JSON_OBJ = re.compile(r"\{.*\}", re.DOTALL)


def judge(
    rubric: str,
    candidate: str,
    model: str | None = None,
    url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict:
    """Ask an evaluator model a YES/NO criterion about `candidate`.

    Returns {passed: bool, evidence: str}. Falls back to passed=False with an
    explanatory evidence string when the judge is unreachable or unparseable,
    so a broken judge never silently inflates the score.
    """
    model = model or os.environ.get("JUDGE_MODEL", DEFAULT_MODEL)
    url = url or os.environ.get("JUDGE_URL", DEFAULT_URL)

    if is_mock(model):
        return {"passed": True, "evidence": "mock-judge"}

    system = (
        "You are a strict evaluator. You are given a CANDIDATE OUTPUT and a "
        "single YES/NO CRITERION. Decide whether the candidate satisfies the "
        "criterion. Reply with ONLY a JSON object: "
        '{"passed": true|false, "evidence": "<=200 char quote or reason"}. '
        "No prose outside the JSON."
    )
    user = f"CRITERION:\n{rubric}\n\nCANDIDATE OUTPUT:\n{candidate}"
    result = chat(system, user, model=model, url=url, temperature=0.0, timeout=timeout)
    if result["error"]:
        return {"passed": False, "evidence": f"judge unreachable: {result['error']}"}

    m = _JSON_OBJ.search(result["content"])
    if not m:
        return {"passed": False, "evidence": "judge returned no JSON"}
    try:
        parsed = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"passed": False, "evidence": "judge JSON parse error"}
    return {
        "passed": bool(parsed.get("passed", False)),
        "evidence": str(parsed.get("evidence", ""))[:300],
    }
