"""Expectation checks — turn one eval expectation into {text, passed, evidence}.

Deterministic checks (contains / not_contains / regex / verdict) need no model
and are reliable. The `llm_judge` check delegates a quality question to an
evaluator model. Every check returns the shape the eval-viewer and
aggregate_benchmark.py expect: keys `text`, `passed`, `evidence`.
"""

import re

from lib import model as model_client


def _contains(output: str, spec: dict) -> tuple[bool, str]:
    low = output.lower()
    all_terms = [t.lower() for t in spec.get("all", [])]
    any_terms = [t.lower() for t in spec.get("any", [])]
    missing = [t for t in all_terms if t not in low]
    any_ok = (not any_terms) or any(t in low for t in any_terms)
    passed = not missing and any_ok
    if passed:
        ev = "all required terms present"
    elif missing:
        ev = f"missing: {', '.join(missing[:5])}"
    else:
        ev = f"none of any-terms found: {', '.join(any_terms[:5])}"
    return passed, ev


def _not_contains(output: str, spec: dict) -> tuple[bool, str]:
    low = output.lower()
    hits = [t for t in spec.get("all", []) if t.lower() in low]
    return (not hits), ("clean" if not hits else f"forbidden present: {', '.join(hits[:5])}")


def _regex(output: str, spec: dict) -> tuple[bool, str]:
    flags = re.IGNORECASE if spec.get("ignorecase", True) else 0
    if spec.get("dotall"):
        flags |= re.DOTALL
    m = re.search(spec["pattern"], output, flags)
    return (m is not None), (f"matched: {m.group(0)[:80]!r}" if m else "no match")


# The verdict skills end on a plain APPROVE / CHANGES NEEDED token. Take the
# LAST such token so a candidate that discusses both but concludes with one
# is scored on its conclusion.
_VERDICT = re.compile(r"\b(CHANGES NEEDED|APPROVE)\b", re.IGNORECASE)


def _verdict(output: str, spec: dict) -> tuple[bool, str]:
    matches = _VERDICT.findall(output)
    if not matches:
        return False, "no APPROVE / CHANGES NEEDED verdict found"
    got = matches[-1].upper()
    want = spec["expected"].upper()
    return (got == want), f"verdict={got} (expected {want})"


def evaluate(expectation: dict, output: str) -> dict:
    """Evaluate one expectation against a candidate output."""
    text = expectation["text"]
    check = expectation.get("check", {})
    ctype = check.get("type")

    if ctype == "contains":
        passed, ev = _contains(output, check)
    elif ctype == "not_contains":
        passed, ev = _not_contains(output, check)
    elif ctype == "regex":
        passed, ev = _regex(output, check)
    elif ctype == "verdict":
        passed, ev = _verdict(output, check)
    elif ctype == "llm_judge":
        res = model_client.judge(check["rubric"], output)
        passed, ev = res["passed"], res["evidence"]
    else:
        passed, ev = False, f"unknown check type: {ctype!r}"

    return {"text": text, "passed": passed, "evidence": ev}
