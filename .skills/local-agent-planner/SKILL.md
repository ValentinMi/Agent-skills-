---
name: local-agent-planner
description: Turn a feature request or coding task into a detailed implementation plan plus a set of small, self-contained task files under a named folder in .opencode/plans/, so a low-context local model (Qwen, Ollama, any small local LLM) can implement them one at a time without re-reading the whole plan. Use this whenever the user wants to break a coding task down into a plan and granular task list, sequence the work into steps, or prepare/hand off tasks for a smaller or local coding model to write — including casual phrasing like "plan this out into tasks", "make me a task list for my local model", "break this feature into steps for qwen", or asking to create a plan under .opencode/plans. This skill only CREATES the plan and task specs — do NOT use it when the user wants you to implement the change yourself now, to just write the code, or to run/execute task files that already exist — only when they want the work broken down and handed off.
---

# Local Agent Planner

This skill helps a strong planning model (you, e.g. Claude Sonnet) act as an **architect** that breaks a coding task into a plan and a set of **small, self-contained task files** that a **weaker local model with limited context** (Qwen, a local Ollama model, etc.) can execute one at a time.

The whole design turns on one constraint: **the executor is not you.** It is a small model that handles code well but gets lost with large context and can't reliably navigate a big document to find "the relevant part." So every task file must hand it exactly what it needs — no more, no less — to do one focused piece of work and verify it.

If the tasks are too big, too vague, or force the executor to reconstruct context by reading the whole plan, the skill has failed. Keep that reader in mind the entire time.

## The two-model setup

- **Planner (you):** big context, strong reasoning, but a *scarce* resource (limited quota). You explore the codebase, make the architectural and design decisions, and write the plan + task specs.
- **Executor (local model):** narrow context, but a capable coder and effectively unlimited to run locally. It opens **one task file at a time** and **writes the actual code**.

The division of labour is the whole point: **you decide *what* to build and give clear technical direction; the executor writes the *how* (the code).** You are spending your scarce reasoning on decisions the small model can't make well — architecture, interfaces, sequencing, edge cases — and delegating the mechanical code-writing to the local model, which is cheap to run and good at it.

So **write specs, not solutions.** Do not hand the executor finished, paste-ready implementations. If you write the whole function body, you've done the executor's job — burning your limited quota and wasting the local model. Instead, pin down the *contract* and the *constraints* precisely enough that a competent coder can only implement it one way, and let it write the code. (The exception is a genuinely tricky or security-sensitive fragment — see "How much to specify" below.)

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

1. **One concern per task — bias toward splitting.** A task should be a single cohesive change: one new module, one endpoint/route, one behaviour, or one tightly-coupled pair (implementation + its test). A small model's typical failure isn't writing bad code — it's *dropping a requirement when juggling several*. A task that says "add hashing AND a login route AND protect the list" is exactly where a weak model does two of three and silently skips the rest. So default to splitting: one route/behaviour per task, even when several land in the same file. Only bundle when the changes are trivial *and* share the exact same context. The cost of more tasks is near zero — they're cheap to generate and the executor reads only one at a time — and smaller tasks give sharper verification: when something breaks you know exactly which task failed. When in doubt, split.

2. **Self-contained.** Everything needed to execute goes *in the task file*: the objective, the minimal context, exact file paths, the interface/contract to satisfy, what to do (not paste-ready code), and how to verify. The executor should never need the plan, other task files, or a broad codebase tour.

3. **Specify the contract, not the implementation.** Pin down the boundary precisely — exact paths (`src/auth/jwt.ts`), exact signatures (`function signToken(userId: string): string`), exact routes/types/schemas, and exact commands (`npm test -- auth`) — because these are decisions the small model can't reliably make and must match across tasks. But stop at the boundary: describe *what the code must do and satisfy*, and let the executor write the body. "Add a function that signs tokens" is too vague (it must invent the interface); pasting the full function is too much (it does the executor's job). The sweet spot is the signature + the behaviour + the constraints.

4. **Verifiable.** Every task ends with a checkable Definition of Done and a concrete verification command (test, build, lint, or a manual check). This lets the executor — and you — know the task actually succeeded before moving on. Verification matters *more* here precisely because the executor, not you, wrote the code: the verify step is how a weaker model catches its own mistakes.

5. **Explicit dependencies and order.** Each task lists its prerequisites by ID. The executor runs them in order; a task can assume everything it depends on is already done, and should state what it can rely on being present.

6. **Right-sized.** Aim for tasks a small model can finish in one focused pass. If a task's steps or context won't fit comfortably in a limited window, that's the signal to split it.

## How much to specify (the code-vs-spec dial)

The default is **spec, not code**: the executor writes the implementation. Calibrate what you provide like this:

- **Always give (the contract):** exact file paths; function/class signatures, types, route shapes, schemas; expected inputs/outputs and status codes; error/edge-case behaviour; naming and which existing pattern to match. These are cross-task decisions the executor can't safely improvise.
- **Give as *hints*, not full code:** which library/API to use and roughly how, the algorithm or sequence of operations in prose, a one- or two-line snippet to illustrate an existing pattern the executor should follow. A short illustrative snippet is fine; a complete solution is not.
- **Let the executor write:** the actual function bodies, the wiring, the boilerplate — the mechanical code that follows unambiguously from the contract.
- **Narrow exception — paste-ready code:** only for a fragment that is genuinely tricky, security-sensitive, or has a non-obvious "one correct form" the small model is likely to get wrong (e.g. a subtle type-narrowing guard, a crypto call with specific parameters). Keep it to that fragment, and say why it's given verbatim. If you find yourself pasting whole files, step back — you're doing the executor's job.

The test: *could a competent coder implement this exactly one way from what I wrote?* If yes, you've specified enough — stop there and let them code. If they'd have to guess at the interface or behaviour, add contract detail (not implementation).

## When several tasks edit the same file

Splitting by concern often means two or three tasks touch the *same* file in sequence (e.g. one file gets a new import, then a new route, then a wrapped handler). The executor runs them one at a time, so by the time it opens task 3, the file no longer looks like the original — tasks 1 and 2 already changed it.

This is the easiest way to feed a small model stale, misleading context. Guard against it:

- **Show the file as it will be when this task runs**, not the original. In "Context you need", describe or quote the *expected current state* after the prerequisite tasks — e.g. "after Task 02, `users.ts` already imports `bcrypt` and defines `SALT_ROUNDS`". Don't paste the pristine original if earlier tasks have moved it on.
- **Anchor the edit unambiguously.** Say where the change goes relative to what's already there ("add the `/login` handler after `/register` and before `GET /`"), so the executor doesn't duplicate or clobber prior work.
- **Order tasks so each builds cleanly on the last**, and state in each task what it can assume is already present (that's what "Depends on" is for).
- If keeping the "current state" description in sync across three tasks becomes fiddly, that's a hint the split is too fine for this file — consider merging those specific edits back into one task.

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
This is what lets the executor work from this file alone. If earlier tasks edited
this same file, describe its state AFTER those edits, not the original — see
"When several tasks edit the same file".>

## Files
- Create: `<path>`
- Modify: `<path>` — <what changes>

## Contract (what your code must satisfy)
<The boundary the executor implements *to* — NOT the implementation itself.
Exact signatures, types, function/route names, schemas, expected inputs/outputs
and status codes. Use a code block for signatures/types. Describe behaviour in
prose. Do not write the function bodies — that's the executor's job.>

## What to do
<Describe the work as instructions, not code: "hash the password with bcrypt
(SALT_ROUNDS = 10) before storing", "look the user up by email, compare with
bcrypt.compare, return 401 on mismatch". Name the library/API and the sequence
of steps. Include a 1–2 line snippet ONLY to show an existing pattern to match.>

## Technical hints
<Optional. Pointers that save the executor time without doing its job: which
helper to reuse, a gotcha in the API, the ESM `.js` import convention, a
type-narrowing caveat. If a fragment is genuinely tricky/security-sensitive and
has one correct form, you may give it verbatim here — and say why.>

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
- [ ] Tasks specify the contract and let the executor write the code — no paste-ready full implementations (except a justified tricky/security-sensitive fragment).
- [ ] Every file path, signature, and command is real (verified against the codebase), not invented.
- [ ] Each task is one concern and small enough for a limited-context model.
- [ ] Dependencies are listed by ID and the order is consistent with them.
- [ ] Each task has a concrete Definition of Done and a verification command.
- [ ] `plan.md` chapters map 1:1 to task files.
- [ ] The user has been told the plan location and execution order.
```
