# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal library of **Agent Skills** (the [anthropics/skills](https://github.com/anthropics/skills) format). There is no application, build, or server here — the "product" is the skills themselves, each a folder that a Claude-family agent loads to gain a specialized capability. This repo is not a Node/Python package; there is no `package.json` or repo-level test runner.

## Architecture: two separate trees, don't conflate them

- **`skills/<name>/`** — the **distributable skills library**: the skills this repo produces (currently the `local-agent-*` trio). These are meant to be deployed *elsewhere* (an OpenCode install, another project) via `install-skills.sh`. Nothing here is symlinked into `.claude/`.
- **`.claude/skills/<name>/`** — skills used **by Claude Code while working on this repo**. Currently just `skill-creator`, Anthropic's meta-skill for authoring/testing/optimizing skills, kept here as real files (not a symlink) because it's a dev-time tool for building this repo's skills, not part of what gets shipped via `install-skills.sh`.

These trees don't mirror each other by design: a skill in `skills/` (built *by* this repo, for *other* agents like a local Qwen model) has no reason to also be a skill Claude Code consults on *this* repo, and vice versa. When adding a new shipped skill, it goes in `skills/` only. When adding a new dev-tool skill for working on this repo, it goes in `.claude/skills/` only.

Anatomy of a skill (`SKILL.md` is the only required file):

```
skills/<name>/
├── SKILL.md            # YAML frontmatter (name, description) + Markdown body
├── scripts/            # executable helpers (optional)
├── references/         # docs loaded on demand (optional)
├── assets/             # templates/files used in output (optional)
└── agents/             # subagent instructions (optional)
```

The frontmatter **`description`** is the primary trigger mechanism — it decides whether the agent consults the skill. Treat it as load-bearing, not a summary.

### Frontmatter gotchas (check after editing)

The `description` value is fussy — two rules that have bitten this repo:

- **No `": "` (colon-space).** YAML parses it as a nested mapping and breaks the whole skill (`mapping values are not allowed in this context`). Use an em dash (`—`).
- **No angle brackets `<` / `>`.** Anthropic's skill validator rejects them (they collide with system-prompt formatting). Put placeholders like `<plan-name>` in the *body*, never in the description — reword the description (e.g. "a named folder in .opencode/plans/").

The authoritative check catches both — run it after any frontmatter edit:

```bash
cd .claude/skills/skill-creator && python -m scripts.quick_validate <path-to-skill>   # prints "Skill is valid!"
```

### Testing skill triggering — do NOT trust `run_eval` here

`run_eval.py`/`run_loop.py` (in `skill-creator`) measure triggering by registering a **slash-command stub** in `.claude/commands/` and watching `claude -p`. In this environment that stub does not trigger, so these tools report **0% (false negatives)** for every query — the number is meaningless here.

To actually test whether a skill triggers, run the **installed** skill directly and look for a `Skill` tool-use referencing the skill name:

```bash
env -u CLAUDECODE claude -p "<realistic user query>" \
  --output-format stream-json --verbose --include-partial-messages \
  | grep -oE '"name":"Skill"|<skill-name>'
```

Note this only proves the skill was *consulted*; a capable model may consult then decline (that can be correct behavior for an out-of-scope query). To judge real behaviour, inspect what it actually produced (e.g. whether it created the expected files), not just whether the name appeared.

## The skills (in `skills/`)

- **`local-agent-planner`** — turns a strong planner (Claude Sonnet) into an architect that writes a `plan.md` plus small, self-contained task specs under `.opencode/plans/<name>/` for a low-context **local** model (Qwen/Ollama) to implement one at a time. Tasks specify the *contract + hints*, not paste-ready code.
- **`local-agent-executor`** — the small local model (Qwen/Ollama on OpenCode) implements the tasks of a plan under `.opencode/plans/` one at a time, one task per fresh context, never loading the whole plan.
- **`local-agent-reviewer`** — reviews one task's diff against that task's own spec before it is marked done; verdict APPROVE / CHANGES NEEDED; reads only the diff plus the task file.

Per-task loop: **plan → execute → verify → review → mark done**.

## skill-creator tooling (in `.claude/skills/`)

Its Python scripts import each other as a package (`from scripts.utils import ...`), so **run them as modules from inside `.claude/skills/skill-creator/`**, not as file paths:

```bash
cd .claude/skills/skill-creator

# Validate a skill's structure/frontmatter
python -m scripts.quick_validate <path-to-skill>

# Trigger-accuracy eval for a description (needs the `claude` CLI)
python -m scripts.run_eval  --skill-path <path> --eval-set <evals.json> --verbose

# Full description-optimization loop
python -m scripts.run_loop  --skill-path <path> --eval-set <evals.json> --model <id> --report none

# Package a skill into a distributable .skill file
python -m scripts.package_skill <path-to-skill>
```

## Conventions

- Skill bodies and generated artifacts are written in **English**; repo prose (README) may be French.
- `.gitignore` excludes `__pycache__/` and `*.pyc` — don't commit compiled Python.
- `install-skills.sh <target-dir> [skill-name ...]` deploys/updates skills from `skills/` into an external skills folder (e.g. an OpenCode install or another project's `.claude/skills`). Re-running it mirrors each skill (stale files removed), so install and update are the same command.
