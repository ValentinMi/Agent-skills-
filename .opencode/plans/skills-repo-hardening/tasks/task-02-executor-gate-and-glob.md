# Task 02 — Executor: reviewer gate + single-plan task discovery

- **ID:** 02 · **Depends on:** 01 · **Plan ref:** plan.md § Task 02 · **Status:** done

## Objective
Two edits in `.skills/local-agent-executor/SKILL.md`: step 7 of "The loop" gains an optional reviewer gate, and the "find next task" snippet targets one plan folder instead of every plan.

## Context
After Task 01 the file references sections `Context`, `What to do`, `Plan ref`. Two spots are still wrong:
1. "The loop" step 7 marks the task `done` directly — but the workflow (see README) has a review step before `done`, using the sibling skill `local-agent-reviewer`. The executor never mentions it.
2. Under "## Finding the next task without loading the plan", the bash snippet globs `.opencode/plans/*/tasks/task-*.md` — with two plans present, their tasks interleave in the sort and the executor can jump between plans.

## Files
- Modify: `.skills/local-agent-executor/SKILL.md` — step 7 of "The loop"; the bash snippet below "Finding the next task without loading the plan"

## Contract
Edit 1 — replace step 7 (currently: `**Mark the task done.** Tick the `Definition of Done` boxes and set the task's `Status` to `done`.`) with wording that keeps the same first sentence structure and adds the gate. Required content:
- If the workflow uses `local-agent-reviewer`, request its review of this task's diff first and only mark `done` on an **APPROVE** verdict; on **CHANGES NEEDED**, apply the fixes, re-run `Verify`, and get re-reviewed.
- Otherwise (no reviewer in use), tick the `Definition of Done` boxes and set `Status` to `done` as before.
- Review stays optional — the executor must still work standalone.

Edit 2 — in the bash snippet, glob one plan: `for f in .opencode/plans/<plan-name>/tasks/task-*.md; do` (keep the rest of the snippet as is). In the sentence introducing the snippet, state that `<plan-name>` is the plan folder being executed. The string `plans/*/tasks` must no longer appear.

Do not renumber steps, do not touch frontmatter, keep the file's terse tone.

## What to do
Apply the two edits above. Keep step 7 to 2–3 sentences; don't describe the reviewer's internals (its own skill covers that).

## Definition of Done
- [ ] Step 7 mentions `local-agent-reviewer`, APPROVE, and CHANGES NEEDED, and keeps review optional
- [ ] Snippet globs `.opencode/plans/<plan-name>/tasks/`; `plans/*/tasks` gone
- [ ] Skill still validates
- [ ] Verify command passes

## Verify
```bash
grep -q 'local-agent-reviewer' .skills/local-agent-executor/SKILL.md \
&& grep -q 'APPROVE' .skills/local-agent-executor/SKILL.md \
&& ! grep -q 'plans/\*/tasks' .skills/local-agent-executor/SKILL.md \
&& grep -q 'plans/<plan-name>/tasks' .skills/local-agent-executor/SKILL.md \
&& (cd .skills/skill-creator && python -m scripts.quick_validate ../local-agent-executor)
```
