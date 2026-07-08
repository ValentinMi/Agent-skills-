# Behavior/quality benchmark for the `local-agent-*` skills

A **runnable kit** that measures whether the three shipped skills actually change
how a *local* model (Qwen/Ollama) behaves — not just whether a description
triggers. You run it **locally, where your model lives**; nothing here calls a
hosted API.

It answers two questions:

1. **with_skill vs without_skill** — does injecting the skill's `SKILL.md` make
   the local model behave better than a plain baseline prompt? (Measured in one
   benchmark run; `aggregate_benchmark.py` reports the delta.)
2. **before vs after** — did an edit to a skill improve or regress its behavior?
   (Run the benchmark twice, then `compare.py` diffs the two runs.)

## How a "skill" is operationalized here

A local model has no skill-loading mechanism — a skill is just instructions you
inject. So:

- **`with_skill`** = the skill's `SKILL.md` body is the system prompt.
- **`without_skill`** = a generic "you are a helpful coding assistant" baseline.

Same task, same model, same grader — the only variable is the skill text. That
isolates the skill's contribution.

## Install / configure

Requires Python 3.10+ (stdlib only — no pip installs) and a running Ollama with
your model pulled:

```bash
ollama pull qwen2.5-coder:7b        # or whatever you run
cp bench/config.example.env bench/config.env   # edit, then: source bench/config.env
```

Key env vars (all optional, defaults in `config.example.env`):

| var | default | meaning |
|-----|---------|---------|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | local chat endpoint |
| `BENCH_MODEL` | `qwen2.5-coder:7b` | model under test (`mock` = no backend) |
| `JUDGE_MODEL` | = `BENCH_MODEL` | grader for `llm_judge` checks |
| `JUDGE_URL` | = `OLLAMA_URL` | grader endpoint |
| `BENCH_TIMEOUT` | `300` | per-request seconds |

## Run it

```bash
# everything, 3 runs per configuration, then aggregate each skill
bench/bench.sh all 3

# one skill
bench/bench.sh reviewer 5

# just the runner (no aggregation), e.g. planner only
python bench/run_bench.py --skill planner --runs 3
```

Output lands under `bench/results/<model>/<skill>/` in the exact layout
skill-creator's `aggregate_benchmark.py` expects:

```
eval-<id>/<config>/run-<k>/grading.json   # machine-graded result
eval-<id>/<config>/run-<k>/output.md      # the model's raw output, for eyeballing
```

`bench.sh` then writes `benchmark.json` + `benchmark.md` per skill. Open the
`benchmark.json` in the eval-viewer for a human read:
`.claude/skills/skill-creator/eval-viewer/`.

## Before/after (regression) comparison

```bash
bench/bench.sh reviewer 3
cp -r bench/results/qwen2.5-coder_7b/reviewer /tmp/reviewer-before

# ...edit skills/local-agent-reviewer/SKILL.md...

bench/bench.sh reviewer 3
python bench/compare.py /tmp/reviewer-before/benchmark.json \
                        bench/results/qwen2.5-coder_7b/reviewer/benchmark.json
```

`compare.py` prints per-config and per-eval pass-rate deltas and **exits 1 if any
eval regressed**, so it drops into CI or a pre-push hook.

## What each skill's evals measure

- **reviewer** (`evals/reviewer.json`) — the cleanest to grade. Each eval hands
  the model a task spec + a diff (fixtures in `fixtures/reviewer/`), some with an
  **injected defect** (DoD violation, scope creep, contract mismatch), one clean.
  Graded deterministically on the **APPROVE / CHANGES NEEDED verdict** plus an
  `llm_judge` check that it cited the right reason.
- **planner** (`evals/planner.json`) — feature request + inline verified codebase
  facts (the harness can't let the model explore a real repo). Graded on: writes
  under `.opencode/plans/`, emits structured task files with Verify + DoD, splits
  by concern with dependencies, and **specs the contract instead of pasting full
  implementations**.
- **executor** (`evals/executor.json`) — a **text proxy** for the dispatcher.
  Given task headers (statuses/deps/Files), does it pick the correct ready set,
  respect the concurrency cap, batch by disjoint Files, and keep the dispatcher
  light? Note this is a proxy: the real skill is tool/subagent-driven, so treat
  these as a check on the model's *dispatch reasoning*, not a full integration
  test.

## Grading

Each expectation has a `check`:

| type | how it's judged |
|------|-----------------|
| `verdict` | last `APPROVE`/`CHANGES NEEDED` token equals `expected` |
| `contains` / `not_contains` | case-insensitive substring presence/absence |
| `regex` | pattern matches the output |
| `llm_judge` | a rubric question → `{passed, evidence}` from `JUDGE_MODEL` |

Deterministic checks are reliable; `llm_judge` is only as good as your judge
model — point `JUDGE_MODEL` at the strongest local model you have. An unreachable
or unparseable judge scores the check **failed** (never a silent pass).

## Extending

Add an object to a skill's `evals/*.json` — `id`, `name`, `prompt`, optional
`fixtures` (paths relative to `bench/`) with `fixture_labels`, and
`expectations`. Give it a `mock_response` if you want `--model mock` to exercise
your new deterministic checks.

## Testing the pipeline without a model

`--model mock` (or `BENCH_MODEL=mock`) skips the backend, returns each eval's
`mock_response`, and mocks the judge — proving the run → grade → aggregate →
compare plumbing end-to-end. It does not produce meaningful *scores*; it proves
the wiring.
