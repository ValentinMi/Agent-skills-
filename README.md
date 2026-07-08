# Agent Skills

A personal library of skills for AI agents (Claude Code, OpenCode, Claude.ai, etc.), in the [Agent Skills](https://github.com/anthropics/skills) format.

Two separate trees (see [`CLAUDE.md`](CLAUDE.md) for the rationale):

- **`skills/<name>/`** — the skills library **produced** by this repo, meant to be deployed elsewhere (`install-skills.sh`).
- **`.claude/skills/<name>/`** — the skills Claude Code uses **to work on this repo itself** (currently `skill-creator`, kept as real files, not a symlink).

```
skills/
├── local-agent-planner/    # Sonnet plans → plan + granular tasks
├── local-agent-executor/   # the local agent (Qwen/OpenCode) runs tasks one at a time
└── local-agent-reviewer/   # reviews a task's diff vs its spec before marking it done

.claude/skills/
└── skill-creator/          # Anthropic's meta-skill (dev-only, not distributed)

bench/                      # local-model behavior/quality benchmark for the skills
```

### local-agent-planner + executor + reviewer (workflow)

A two-model workflow that spares a strong model and puts a local model to work:

- [`local-agent-planner`](skills/local-agent-planner/SKILL.md) — a strong model (Claude Sonnet) breaks a coding task into a `plan.md` + **self-contained** task files under `.opencode/plans/<name>/`. Tasks give the *contract + hints*, not paste-ready code.
- [`local-agent-executor`](skills/local-agent-executor/SKILL.md) — a small local model (Qwen on OpenCode) implements those tasks **one at a time**, never loading the whole plan, to keep its context/RAM light.
- [`local-agent-reviewer`](skills/local-agent-reviewer/SKILL.md) — reviews a **task's diff** against its spec (Contract, Definition of Done, Constraints) before it is marked done, returning an *APPROVE* / *CHANGES NEEDED* verdict. Light context: only the current diff + the task file, never the whole plan.

Per-task loop: **plan → execute → verify → review → mark done**.

### skill-creator

Anthropic's official [`skill-creator`](.claude/skills/skill-creator/SKILL.md): create a skill from scratch, improve an existing one, run evals, optimize the description (triggering), package into a `.skill`. Used to build the skills in `skills/` — it is not itself distributed by `install-skills.sh`.
Source: [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator).

Every new skill meant for distribution goes in `skills/<name>/`.

## Benchmark (`bench/`)

A runnable kit that measures whether the `local-agent-*` skills actually change how a **local** model (Qwen/Ollama) behaves — you run it locally, where your model lives. Two axes:

- **with_skill vs without_skill** — the `SKILL.md` body injected as the system prompt vs a generic baseline; the delta `aggregate_benchmark.py` already reports.
- **before vs after** — run twice, then `compare.py` diffs two `benchmark.json` and exits non-zero on any per-eval regression.

Results are written in the layout skill-creator's `aggregate_benchmark.py` consumes, so they open in the `eval-viewer`. A `--model mock` mode exercises the whole pipeline with no backend. Full usage in [`bench/README.md`](bench/README.md).

```bash
ollama pull qwen2.5-coder:7b
cp bench/config.example.env bench/config.env   # edit, then: source bench/config.env
bench/bench.sh all 3
```

## Install / update the skills elsewhere

`install-skills.sh` copies the skills from `skills/` into a target skills folder (OpenCode, a project's `.claude/skills`, etc.). Re-running it updates: each skill is **mirrored** (files removed from a skill are removed in the target too); `__pycache__`/`*.pyc` are never copied.

```bash
./install-skills.sh <target-dir>                       # all skills
./install-skills.sh <target-dir> local-agent-executor  # a specific skill

# examples
./install-skills.sh ~/.config/opencode/skills
./install-skills.sh ../my-project/.claude/skills local-agent-planner local-agent-executor
```
