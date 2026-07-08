#!/usr/bin/env python3
"""Before/after regression comparison of two benchmark.json files.

Run the benchmark once, edit a skill, run it again, then:

    python bench/compare.py BEFORE/benchmark.json AFTER/benchmark.json

Prints per-configuration and per-eval mean pass-rate for both runs and the
delta, flagging any eval whose pass-rate dropped (a regression).
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def per_eval_pass_rate(benchmark: dict) -> dict[tuple[str, int], float]:
    """Mean pass_rate keyed by (configuration, eval_id) from the runs array."""
    buckets: dict[tuple[str, int], list[float]] = defaultdict(list)
    for run in benchmark.get("runs", []):
        key = (run["configuration"], run["eval_id"])
        buckets[key].append(run["result"]["pass_rate"])
    return {k: sum(v) / len(v) for k, v in buckets.items()}


def config_pass_rate(benchmark: dict) -> dict[str, float]:
    summary = benchmark.get("run_summary", {})
    return {
        cfg: data.get("pass_rate", {}).get("mean", 0.0)
        for cfg, data in summary.items()
        if cfg != "delta"
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("before", type=Path, help="earlier benchmark.json")
    parser.add_argument("after", type=Path, help="later benchmark.json")
    args = parser.parse_args()

    before = json.loads(args.before.read_text())
    after = json.loads(args.after.read_text())

    b_cfg, a_cfg = config_pass_rate(before), config_pass_rate(after)
    b_eval, a_eval = per_eval_pass_rate(before), per_eval_pass_rate(after)

    print("=== Overall pass-rate by configuration ===")
    print(f"{'config':<16}{'before':>9}{'after':>9}{'delta':>9}")
    for cfg in sorted(set(b_cfg) | set(a_cfg)):
        bv, av = b_cfg.get(cfg, 0.0), a_cfg.get(cfg, 0.0)
        print(f"{cfg:<16}{bv*100:>8.0f}%{av*100:>8.0f}%{(av-bv)*100:>+8.0f}%")

    print("\n=== Per-eval pass-rate ===")
    print(f"{'config / eval':<26}{'before':>9}{'after':>9}{'delta':>9}")
    regressions = []
    for key in sorted(set(b_eval) | set(a_eval)):
        cfg, eid = key
        bv, av = b_eval.get(key, 0.0), a_eval.get(key, 0.0)
        delta = av - bv
        flag = "  <-- REGRESSION" if delta < -1e-9 else ""
        if delta < -1e-9:
            regressions.append((cfg, eid, delta))
        print(f"{cfg + ' / eval-' + str(eid):<26}"
              f"{bv*100:>8.0f}%{av*100:>8.0f}%{delta*100:>+8.0f}%{flag}")

    if regressions:
        print(f"\n{len(regressions)} regression(s) detected.")
        sys.exit(1)
    print("\nNo regressions.")


if __name__ == "__main__":
    main()
