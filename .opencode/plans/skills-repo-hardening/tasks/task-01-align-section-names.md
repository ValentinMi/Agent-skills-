# Task 01 — Align task-file section names across the three skills

- **ID:** 01 · **Depends on:** none · **Plan ref:** plan.md § Task 01 · **Status:** todo

## Objective
Make executor and reviewer reference the exact section names the planner's task template emits: `Context`, `What to do` (constraints folded in), `Plan ref`.

## Context
`.skills/local-agent-planner/SKILL.md` contains a task-file template whose sections are `## Objective`, `## Context`, `## Files`, `## Contract`, `## What to do`, `## Definition of Done`, `## Verify`, with a meta line `**Plan ref:** plan.md § Task 01`. There is NO `Context you need`, `Constraints & gotchas`, or `Plan reference` section — but the other two skills (and one line of the planner itself) still use those old names.

## Files
- Modify: `.skills/local-agent-planner/SKILL.md` — 1 occurrence
- Modify: `.skills/local-agent-executor/SKILL.md` — 6 occurrences
- Modify: `.skills/local-agent-reviewer/SKILL.md` — 2 occurrences

## Contract
Text-only renames; do not add/remove sections, do not touch YAML frontmatter, keep everything else verbatim.

Planner (workflow step 4, ~line 39):
- `` Add `Plan reference: plan.md § Task NN` `` → `` Add `Plan ref: plan.md § Task NN` ``

Executor:
- Every `` `Context you need` `` → `` `Context` `` (lines ~18, ~28, ~30 — 3 occurrences)
- Every `` `Plan reference` `` → `` `Plan ref` `` (lines ~18, ~46 — 2 occurrences)
- Step 5 (~line 20): `` Respect `Constraints & gotchas`. `` → `` Respect the constraints and gotchas folded into `What to do`. ``

Reviewer:
- ~Line 22: `` `Contract`, `What to do`, `Constraints & gotchas`, and `Definition of Done` `` → `` `Contract`, `What to do` (constraints and gotchas are folded in there), and `Definition of Done` ``
- ~Line 28 checklist bullet: `**Constraints & gotchas respected** — the things the task said to match, reuse, or not touch.` → `**Constraints respected** — the gotchas folded into `What to do`: things the task said to match, reuse, or not touch.`

## What to do
Search each file for the three old strings and apply the replacements above. Nothing else changes.

## Definition of Done
- [ ] `Context you need`, `Constraints & gotchas`, `Plan reference` appear in none of the three files
- [ ] All three skills still validate
- [ ] Verify command passes

## Verify
```bash
! grep -rn 'Context you need\|Constraints & gotchas\|Plan reference' \
  .skills/local-agent-planner/SKILL.md \
  .skills/local-agent-executor/SKILL.md \
  .skills/local-agent-reviewer/SKILL.md \
&& (cd .skills/skill-creator \
    && python -m scripts.quick_validate ../local-agent-planner \
    && python -m scripts.quick_validate ../local-agent-executor \
    && python -m scripts.quick_validate ../local-agent-reviewer)
```
