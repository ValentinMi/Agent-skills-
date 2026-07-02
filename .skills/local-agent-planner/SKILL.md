---
name: local-agent-planner
description: Turn a feature request or coding task into a detailed implementation plan plus a set of small, self-contained task files under .opencode/plans/<plan-name>/, designed so a low-context local model (Qwen, Ollama, any small local LLM) can execute them one at a time without re-reading the whole plan. Use this whenever the user — especially in plan mode — wants to break work down, create a plan and task list, split a feature into steps, or prepare tasks to hand off to a smaller/local coding model. Trigger even on casual phrasing like "plan this out", "make me a task list", "break this into tasks for my local model", or when the user mentions .opencode/plans or handing work to a local agent.
---

# Local Agent Planner

This skill helps a strong planning model (you, e.g. Claude Sonnet) act as an **architect** that breaks a coding task into a plan and a set of **small, self-contained task files** that a **weaker local model with limited context** (Qwen, a local Ollama model, etc.) can execute one at a time.

The whole design turns on one constraint: **the executor is not you.** It is a small model that handles code well but gets lost with large context and can't reliably navigate a big document to find "the relevant part." So every task file must hand it exactly what it needs — no more, no less — to do one focused piece of work and verify it.

If the tasks are too big, too vague, or force the executor to reconstruct context by reading the whole plan, the skill has failed. Keep that reader in mind the entire time.

## The two-model setup

- **Planner (you):** big context, strong reasoning. You explore the codebase, make architectural decisions, and write the plan + tasks.
- **Executor (local model):** narrow context, good at writing code from a precise spec. It opens **one task file at a time** and implements it.

You do the thinking so the executor doesn't have to.

## Output structure

Create this under the repo root:

```
.opencode/plans/<plan-name>/
├── plan.md          # overview, decisions, conventions, task index (dependencies + status)
└── tasks/
    ├── task-01-<slug>.md
    ├── task-02-<slug>.md
    └── ...
```

- `<plan-name>` is a short kebab-case name for the feature/change (e.g. `add-jwt-auth`, `refactor-cart-service`).
- Task files are zero-padded and slugged so ordering is obvious: `task-01-create-user-model.md`.
- All generated files are written in **English**.

## Workflow

### 1. Understand and explore first — never plan in the abstract

The single biggest quality lever is grounding the plan in the **real** codebase. Before writing anything:

- Read the relevant existing files. Note exact paths, function/class signatures, types, and patterns already in use.
- Identify the project's conventions: language/framework, how tests are run, how to build/lint, directory layout, naming style.
- Figure out the real seams where the change lands.

A small executor model cannot discover this itself reliably. Anything you don't pin down now, it will guess — usually wrong. So every file path, signature, and command you put in a task should be one you actually verified, not invented.

If the request is ambiguous in a way that changes the plan, ask the user before writing files.

### 2. Name the plan and create the folders

Pick `<plan-name>`, then create `.opencode/plans/<plan-name>/tasks/`.

### 3. Write `plan.md`

Use the template below. `plan.md` is the human/architect view and the source of truth for ordering and decisions. It is **not** required reading for the executor on any single task — the task files stand on their own.

### 4. Write the task files

One file per task, using the task template below. This is where the skill earns its keep. Each task must be **self-contained**: the executor should be able to complete it by reading only that one file. Include a pointer back to the matching `plan.md` chapter as a fallback (`Plan reference: plan.md § Task 3`), but never rely on the executor following it.

### 5. Review pass — read each task as if you were the small model

Re-open each task file and ask: "If I had never seen the plan or the codebase overview, could I do exactly this and know when I'm done?" Fix anything that fails that test. This pass matters more than the first draft.

### 6. Tell the user

Report the plan path, the number of tasks, and the suggested execution order. Offer to adjust granularity.

## Design principles for tasks

Explain these to yourself as you write — they're the reason for the format, not arbitrary rules.

1. **One concern per task.** A task should be a single cohesive change — typically one file or one tightly-coupled pair (implementation + its test). A small model does one narrow thing well and flails when juggling several. When in doubt, split.

2. **Self-contained.** Everything needed to execute goes *in the task file*: the objective, the minimal context, exact file paths, the interfaces/signatures to implement, step-by-step instructions, and how to verify. The executor should never need the plan, other task files, or a broad codebase tour.

3. **Concrete over descriptive.** Give exact paths (`src/auth/jwt.ts`), exact signatures (`function signToken(userId: string): string`), and exact commands (`npm test -- auth`). "Add a function that signs tokens" forces the small model to invent an interface; give it the interface.

4. **Verifiable.** Every task ends with a checkable Definition of Done and a concrete verification command (test, build, lint, or a manual check). This lets the executor — and you — know the task actually succeeded before moving on.

5. **Explicit dependencies and order.** Each task lists its prerequisites by ID. The executor runs them in order; a task can assume everything it depends on is already done, and should state what it can rely on being present.

6. **Right-sized.** Aim for tasks a small model can finish in one focused pass. If a task's steps or context won't fit comfortably in a limited window, that's the signal to split it.

## `plan.md` template

```markdown
# Plan: <Human-readable title>

## Goal
<1–3 sentences: what we're building/changing and why.>

## Current state
<Brief: the relevant existing code, its shape, and where the change lands. Real paths.>

## Approach & key decisions
<The chosen strategy and any decisions the executor must respect — data shapes,
patterns to follow, libraries to use, things to avoid. Bullet points.>

## Conventions (apply to every task)
- Language / framework: <e.g. TypeScript, Node 20>
- Run tests: `<command>`
- Build: `<command>`
- Lint / format: `<command>`
- Other: <naming, file layout, error-handling patterns, etc.>

## Task index
| ID | Task | Depends on | Status |
|----|------|-----------|--------|
| 01 | <title> | — | [ ] |
| 02 | <title> | 01 | [ ] |
| 03 | <title> | 01, 02 | [ ] |

## Task 01 — <title>
<A short chapter (a few sentences to a paragraph) describing this task's slice of
the work in prose. This is the fallback detail a task file points back to. Keep
each chapter focused on one task so a task can reference "§ Task 01" alone.>

## Task 02 — <title>
<...>
```

Keep chapters aligned 1:1 with tasks so `Plan reference: plan.md § Task NN` always points at exactly the right slice.

## Task file template

````markdown
# Task 01 — <title>

- **ID:** 01
- **Depends on:** <task IDs, or "none">
- **Plan reference:** plan.md § Task 01
- **Status:** todo

## Objective
<1–2 sentences: what this task accomplishes.>

## Context you need
<The minimal slice of context required to do THIS task without reading anything
else: the relevant existing code/signatures (quote the actual snippet if small),
data shapes, and what previous tasks have already produced that you can rely on.
This is what lets the executor work from this file alone.>

## Files
- Create: `<path>`
- Modify: `<path>` — <what changes>

## Interface / contract
<Exact signatures, types, function names, routes, schemas to implement. Be
precise enough that there's no guessing. Use a code block.>

## Steps
1. <imperative step>
2. <imperative step>
3. <...>

## Constraints & gotchas
<Anything easy to get wrong: edge cases, patterns to match, things NOT to touch,
imports to reuse, error handling expected.>

## Definition of Done
- [ ] <objective, checkable outcome>
- [ ] <another>
- [ ] Verification command passes (below)

## Verify
```bash
<exact command to prove the task works, e.g. `npm test -- auth/jwt`>
```
````

## Quality checklist before you finish

- [ ] Every task reads as self-contained — no task requires the plan or a codebase tour to execute.
- [ ] Every file path, signature, and command is real (verified against the codebase), not invented.
- [ ] Each task is one concern and small enough for a limited-context model.
- [ ] Dependencies are listed by ID and the order is consistent with them.
- [ ] Each task has a concrete Definition of Done and a verification command.
- [ ] `plan.md` chapters map 1:1 to task files.
- [ ] The user has been told the plan location and execution order.
```
