# Task 03 — CLAUDE.md: document all four skills

- **ID:** 03 · **Depends on:** none · **Plan ref:** plan.md § Task 03 · **Status:** todo

## Objective
Replace the outdated `## The two skills` section of `CLAUDE.md` with one covering all four skills and the per-task workflow loop.

## Context
`CLAUDE.md` (repo root) has a section `## The two skills` listing only `skill-creator` and `local-agent-planner`. The repo now also has `.skills/local-agent-executor/` and `.skills/local-agent-reviewer/`. `README.md` §"local-agent-planner + executor + reviewer (workflow)" already describes the trio accurately (in French) — use it as the factual source, but write CLAUDE.md in English.

## Files
- Modify: `CLAUDE.md` — only the `## The two skills` section; everything else stays byte-identical

## Contract
- New heading: `## The skills` (replaces `## The two skills`).
- One bullet per skill, same style as the existing two bullets (bold name, em-dash, 1–3 lines):
  - `skill-creator` — keep the existing bullet unchanged.
  - `local-agent-planner` — keep the existing bullet unchanged.
  - `local-agent-executor` — small local model (Qwen/Ollama on OpenCode) implements the tasks of a plan under `.opencode/plans/` one at a time, one task per fresh context, never loading the whole plan.
  - `local-agent-reviewer` — reviews one task's diff against that task's own spec before it is marked done; verdict APPROVE / CHANGES NEEDED; reads only the diff + the task file.
- After the bullets, one line stating the per-task loop: plan → execute → verify → review → mark done.
- Do not change any other section of CLAUDE.md.

## What to do
Rewrite that one section per the contract. Keep it as terse as the current bullets.

## Definition of Done
- [ ] `The two skills` heading gone; all four skill names present in CLAUDE.md
- [ ] Loop line present; rest of the file untouched (check with `git diff CLAUDE.md`)
- [ ] Verify command passes

## Verify
```bash
! grep -q 'The two skills' CLAUDE.md \
&& grep -q 'local-agent-executor' CLAUDE.md \
&& grep -q 'local-agent-reviewer' CLAUDE.md \
&& grep -q 'local-agent-planner' CLAUDE.md \
&& grep -q 'skill-creator' CLAUDE.md
```
