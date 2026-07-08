#!/usr/bin/env python3
"""Run the behavior/quality benchmark for one local-agent skill.

For each eval, runs the local model under two configurations —
`with_skill` (the skill's SKILL.md body injected as the system prompt) and
`without_skill` (a generic baseline system prompt) — N times each, grades every
run against the eval's expectations, and writes results in the directory layout
that skill-creator's aggregate_benchmark.py consumes:

    <out>/<skill>/eval-<id>/<config>/run-<k>/grading.json

Then point aggregate_benchmark.py at <out>/<skill> to get benchmark.json.

Example (real model):
    OLLAMA_URL=http://localhost:11434/api/chat BENCH_MODEL=qwen2.5-coder:7b \
      python bench/run_bench.py --skill reviewer --runs 3

Example (plumbing test, no backend):
    python bench/run_bench.py --skill reviewer --runs 1 --model mock
"""

import argparse
import json
import sys
from pathlib import Path

BENCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = BENCH_DIR.parent
if str(BENCH_DIR) not in sys.path:
    sys.path.insert(0, str(BENCH_DIR))

from lib import checks, model as model_client  # noqa: E402

SKILLS = ["planner", "executor", "reviewer"]

BASELINE_SYSTEM = (
    "You are a helpful, capable coding assistant. Read the user's request "
    "carefully and complete it as well as you can."
)


def load_skill_body(skill: str) -> str:
    """Return the SKILL.md markdown body (frontmatter stripped)."""
    path = REPO_ROOT / "skills" / f"local-agent-{skill}" / "SKILL.md"
    text = path.read_text()
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def build_user_prompt(eval_item: dict) -> str:
    """Eval prompt plus any referenced fixture files, each under a header."""
    sections = [eval_item["prompt"].strip()]
    for rel in eval_item.get("fixtures", []):
        fpath = BENCH_DIR / rel
        content = fpath.read_text()
        label = eval_item.get("fixture_labels", {}).get(rel, rel)
        sections.append(f"\n--- {label} ---\n{content}")
    return "\n".join(sections)


def grade_output(eval_item: dict, output: str, model_error: str | None,
                 seconds: float) -> dict:
    """Grade one run's output → grading.json in aggregate_benchmark format."""
    expectations = [checks.evaluate(exp, output) for exp in eval_item["expectations"]]
    passed = sum(1 for e in expectations if e["passed"])
    total = len(expectations)

    notes = {"uncertainties": [], "needs_review": [], "workarounds": []}
    if model_error:
        notes["needs_review"].append(f"model call errored: {model_error}")
    if not output.strip():
        notes["needs_review"].append("empty model output")

    return {
        "summary": {
            "pass_rate": round(passed / total, 4) if total else 0.0,
            "passed": passed,
            "failed": total - passed,
            "total": total,
        },
        "timing": {"total_duration_seconds": round(seconds, 2)},
        "execution_metrics": {
            "total_tool_calls": 0,
            "output_chars": len(output),
            "errors_encountered": 1 if model_error else 0,
        },
        "expectations": expectations,
        "user_notes_summary": notes,
    }


def run_skill(skill: str, eval_set: list[dict], out_dir: Path, runs: int,
              model: str, temperature: float, configs: dict[str, str]) -> None:
    skill_out = out_dir / skill
    for eval_item in eval_set:
        eid = eval_item["id"]
        user_prompt = build_user_prompt(eval_item)
        for config, system_prompt in configs.items():
            for k in range(1, runs + 1):
                run_dir = skill_out / f"eval-{eid}" / config / f"run-{k}"
                run_dir.mkdir(parents=True, exist_ok=True)

                res = model_client.chat(
                    system=system_prompt,
                    user=user_prompt,
                    model=model,
                    temperature=temperature,
                    mock_response=eval_item.get("mock_response", ""),
                )
                grading = grade_output(eval_item, res["content"], res["error"],
                                       res["seconds"])

                (run_dir / "grading.json").write_text(json.dumps(grading, indent=2))
                (run_dir / "output.md").write_text(res["content"])
                pr = grading["summary"]["pass_rate"]
                print(f"  [{skill}] eval-{eid} {config} run-{k}: "
                      f"{pr*100:.0f}% ({grading['summary']['passed']}/"
                      f"{grading['summary']['total']})")

        # eval_metadata so aggregate keeps stable eval ids
        (skill_out / f"eval-{eid}" / "eval_metadata.json").write_text(
            json.dumps({"eval_id": eid, "name": eval_item.get("name", "")}, indent=2)
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skill", default="all",
                        help="planner | executor | reviewer | all (default: all)")
    parser.add_argument("--runs", type=int, default=3,
                        help="runs per configuration (default: 3)")
    parser.add_argument("--model", default=model_client.DEFAULT_MODEL,
                        help="model name; 'mock' skips the backend")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--out", type=Path, default=None,
                        help="output dir (default: bench/results/<model>)")
    args = parser.parse_args()

    targets = SKILLS if args.skill == "all" else [args.skill]
    for t in targets:
        if t not in SKILLS:
            parser.error(f"unknown skill {t!r}; choose from {SKILLS} or 'all'")

    # In mock mode the judge must also be mocked, otherwise llm_judge checks
    # would try to reach a real (absent) backend and spuriously fail.
    if model_client.is_mock(args.model):
        import os
        os.environ["BENCH_MOCK"] = "1"

    out_dir = args.out or (BENCH_DIR / "results" / args.model.replace(":", "_"))
    out_dir.mkdir(parents=True, exist_ok=True)

    for skill in targets:
        eval_path = BENCH_DIR / "evals" / f"{skill}.json"
        eval_set = json.loads(eval_path.read_text())
        configs = {
            "with_skill": load_skill_body(skill),
            "without_skill": BASELINE_SYSTEM,
        }
        print(f"== {skill}: {len(eval_set)} evals x {len(configs)} configs "
              f"x {args.runs} runs (model={args.model}) ==")
        run_skill(skill, eval_set, out_dir, args.runs, args.model,
                  args.temperature, configs)

    print(f"\nResults written under: {out_dir}")
    print("Next: aggregate each skill, e.g.")
    for skill in targets:
        print(f"  python .claude/skills/skill-creator/scripts/aggregate_benchmark.py "
              f"{out_dir / skill} --skill-name local-agent-{skill}")


if __name__ == "__main__":
    main()
