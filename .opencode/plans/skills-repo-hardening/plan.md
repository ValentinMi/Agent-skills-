# Plan: Skills repo hardening

## Goal
Fix consistency bugs found in review: the three `local-agent-*` skills reference task-file section names that the planner's template no longer emits; the executor never invokes the reviewer gate and its next-task script mixes plans; CLAUDE.md documents only 2 of 4 skills; nothing validates skills in CI; install-skills.sh can overwrite its own source through symlinks.

## Current state
- `.skills/local-agent-planner/SKILL.md` — template emits `## Context`, `## What to do` (constraints folded in), meta line `**Plan ref:** plan.md § Task NN`. But its own workflow step 4 (line 39) still says `Plan reference:`.
- `.skills/local-agent-executor/SKILL.md` — references stale names `Context you need` (lines 18, 28, 30), `Constraints & gotchas` (line 20), `Plan reference` (lines 18, 46). Step 7 (line 22) marks tasks `done` without the reviewer gate. Bash snippet (lines 36–40) globs `.opencode/plans/*/tasks/` — all plans at once.
- `.skills/local-agent-reviewer/SKILL.md` — references stale `Constraints & gotchas` (lines 22, 28).
- `CLAUDE.md` — section `## The two skills` lists only skill-creator and local-agent-planner.
- No `.github/` directory; no CI.
- `install-skills.sh` — mirrors `.skills/<name>/` into `<target>/<name>/` with rsync `--delete` (or rm+cp fallback); no check that target ≠ source, so installing into this repo's own `.claude/skills/` (symlinks to `.skills/`) writes the source onto itself.

## Approach & key decisions
- **Canonical section names = the planner's template** (it generates the files): `Context`, `What to do`, `Plan ref`. Executor and reviewer align to it; constraints/gotchas live inside `What to do`.
- Reviewer gate is **optional** in the executor: "if the workflow uses local-agent-reviewer, mark done only after APPROVE". Don't make review mandatory — executor must still work standalone.
- CI validates with the repo's own tool: `python -m scripts.quick_validate` run from `.skills/skill-creator/` (only dep: `pyyaml`), plus a symlink check `.claude/skills/<name>` → `../../.skills/<name>`.
- install-skills.sh guardrail = **realpath comparison** (global: target dir vs `.skills`; per-skill: dst vs src). Dropped "validate before copy" — it would add a Python dependency to a pure-bash script and CI (Task 04) already validates at the source.
- Skill SKILL.md files stay in English. No frontmatter edits anywhere, but re-run quick_validate after every SKILL.md edit anyway.

## Conventions (every task)
- Files: Markdown (skill docs), YAML (workflow), Bash (`set -euo pipefail` style already in install-skills.sh).
- Validate a skill: `cd .skills/skill-creator && python -m scripts.quick_validate ../<skill-name>` → prints `Skill is valid!`.
- All skill/plan content in English.
- Don't touch `.skills/skill-creator/` (verbatim import from anthropics/skills).

## Task index
| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| 01 | Align task-file section names across the three skills | — | [ ] |
| 02 | Executor: reviewer gate + single-plan task discovery | 01 | [ ] |
| 03 | CLAUDE.md: document all four skills | — | [ ] |
| 04 | CI workflow validating skills and symlinks | — | [ ] |
| 05 | install-skills.sh: refuse to overwrite its own source | — | [ ] |

## Task 01 — Align task-file section names
The planner's compressed template renamed sections but executor/reviewer (and one line of the planner itself) still use the old names. Pure mechanical rename in three SKILL.md files: `Context you need` → `Context`, `Plan reference` → `Plan ref`, and `Constraints & gotchas` → rephrased as constraints folded into `What to do`.

## Task 02 — Executor: reviewer gate + single-plan glob
Two small edits to the executor, in different sections, after Task 01's renames: step 7 gains the optional local-agent-reviewer gate; the "find next task" bash snippet targets one plan folder instead of `plans/*/`.

## Task 03 — CLAUDE.md skills section
Replace `## The two skills` with a section covering all four skills and the per-task loop (plan → execute → verify → review → mark done), mirroring what README.md already says.

## Task 04 — CI workflow
New `.github/workflows/validate-skills.yml`: on push + PR, install pyyaml, run quick_validate on every `.skills/*/` containing a SKILL.md, and check each has a `.claude/skills/<name>` symlink resolving to it.

## Task 05 — install-skills.sh guardrail
Abort if the target dir resolves to `.skills`; per skill, skip (and count as failed) when the destination resolves to the source directory (the symlink case).
