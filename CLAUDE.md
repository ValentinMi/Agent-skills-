# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A personal library of **Agent Skills** (the [anthropics/skills](https://github.com/anthropics/skills) format). There is no application, build, or server here — the "product" is the skills themselves, each a folder that a Claude-family agent loads to gain a specialized capability. This repo is not a Node/Python package; there is no `package.json` or repo-level test runner.

## Architecture: source vs. discovery (the key thing to get right)

Skills live in **two places that must stay in sync**:

- `.skills/<name>/` — the **source of truth**. Real files live here.
- `.claude/skills/<name>` — a **symlink** back to `../../.skills/<name>`. This is the path Claude Code actually scans to discover skills.

A skill only becomes usable once its symlink exists. **When you add a skill, you must create the symlink**, or Claude Code won't see it:

```bash
ln -s ../../.skills/<name> .claude/skills/<name>
```

Anatomy of a skill (`SKILL.md` is the only required file):

```
.skills/<name>/
├── SKILL.md            # YAML frontmatter (name, description) + Markdown body
├── scripts/            # executable helpers (optional)
├── references/         # docs loaded on demand (optional)
├── assets/             # templates/files used in output (optional)
└── agents/             # subagent instructions (optional)
```

The frontmatter **`description`** is the primary trigger mechanism — it decides whether the agent consults the skill. Treat it as load-bearing, not a summary.

### Frontmatter gotchas (validate after editing)

The `description` value is fussy — two rules that have bitten this repo:

- **No `": "` (colon-space).** YAML parses it as a nested mapping and breaks the whole skill (`mapping values are not allowed in this context`). Use an em dash (`—`).
- **No angle brackets `<` / `>`.** The skill validator rejects them (they collide with system-prompt formatting). Put placeholders like `<plan-name>` in the *body*, never in the description — reword the description (e.g. "a named folder in .opencode/plans/").

The authoritative check catches both — run it after any frontmatter edit:

```bash
cd .skills/skill-creator && python -m scripts.quick_validate <path-to-skill>   # prints "Skill is valid!"
```

## The skills

- **`skill-creator`** — Anthropic's meta-skill for authoring, evaluating, and optimizing other skills (imported verbatim from anthropics/skills; contains Python tooling). Invoke it whenever creating or improving a skill.
- **`local-agent-planner`** — turns a strong planner (Claude Sonnet) into an architect that writes a `plan.md` plus small, self-contained task specs under `.opencode/plans/<name>/` for a low-context **local** model (Qwen/Ollama) to implement one at a time. Tasks specify the *contract + hints*, not paste-ready code.
- **`local-agent-executor`** — the small local model (Qwen/Ollama on OpenCode) implements the tasks of a plan under `.opencode/plans/` one at a time, one task per fresh context, never loading the whole plan.
- **`local-agent-reviewer`** — reviews one task's diff against that task's own spec before it is marked done; verdict APPROVE / CHANGES NEEDED; reads only the diff plus the task file.

Per-task loop: **plan → execute → verify → review → mark done**.

## skill-creator tooling

Its Python scripts import each other as a package (`from scripts.utils import ...`), so **run them as modules from inside `.skills/skill-creator/`**, not as file paths:

```bash
cd .skills/skill-creator

# Validate a skill's structure/frontmatter
python -m scripts.quick_validate <path-to-skill>

# Trigger-accuracy eval for a description (needs the `claude` CLI)
python -m scripts.run_eval  --skill-path <path> --eval-set <evals.json> --verbose

# Full description-optimization loop
python -m scripts.run_loop  --skill-path <path> --eval-set <evals.json> --model <id> --report none

# Package a skill into a distributable .skill file
python -m scripts.package_skill <path-to-skill>
```

### Testing skill triggering — do NOT trust `run_eval` here

`run_eval.py`/`run_loop.py` measure triggering by registering a **slash-command stub** in `.claude/commands/` and watching `claude -p`. In this environment that stub does not trigger, so these tools report **0% (false negatives)** for every query — the number is meaningless here.

To actually test whether a skill triggers, run the **installed** skill directly and look for a `Skill` tool-use referencing the skill name:

```bash
env -u CLAUDECODE claude -p "<realistic user query>" \
  --output-format stream-json --verbose --include-partial-messages \
  | grep -oE '"name":"Skill"|<skill-name>'
```

Note this only proves the skill was *consulted*; a capable model may consult then decline. To judge real behaviour, inspect what it actually produced (e.g. whether it created files), not just whether the name appeared.

## Conventions

- Skill bodies and generated artifacts are written in **English**; repo prose (README) may be French.
- `.gitignore` excludes `__pycache__/` and `*.pyc` — don't commit compiled Python.
- Keep `.skills/` and `.claude/skills/` in lockstep: every source folder has a matching symlink.
