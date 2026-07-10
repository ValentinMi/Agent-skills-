---
name: local-agent-planner
description: Turn a feature request or coding task into a detailed implementation plan plus a set of small, self-contained task files under a named folder in .opencode/plans/, so a low-context local model (Qwen, Ollama, any small local LLM) can implement them one at a time without re-reading the whole plan. Use this whenever the user wants to break a coding task down into a plan and granular task list, sequence the work into steps, or prepare/hand off tasks for a smaller or local coding model to write — including casual phrasing like "plan this out into tasks", "make me a task list for my local model", "break this feature into steps for qwen", or asking to create a plan under .opencode/plans. This skill only CREATES the plan and task specs — do NOT use it when the user wants you to implement the change yourself now, to just write the code, or to run/execute task files that already exist — only when they want the work broken down and handed off.
---

# Local Agent Planner

You (a strong planner, e.g. Claude Sonnet) act as an **architect**: you break a coding task into a plan and a set of **small, self-contained task files** that a **weaker local model with limited context** (Qwen, Ollama, etc.) executes one at a time.

The design turns on one constraint: **the executor is not you.** It's a small model — good at code, but lost in large context and unable to navigate a big document to find "the relevant part." So each task file hands it exactly what it needs, no more, to do one focused piece of work and verify it.

**Division of labour:** you decide *what* to build (architecture, interfaces, sequencing, edge cases) — decisions the small model can't make. The executor writes the *how* (the code). So **write specs, not solutions.** Pin down the *contract* precisely enough that a competent coder can implement it one way; let it write the body. Writing full function bodies burns your scarce quota and wastes the executor. (Exception: a genuinely tricky/security-sensitive fragment — see the dial below.)

## Economy is quality, not a trade-off

Your tokens are the scarce resource — spend the fewest that still make each task unambiguous. This is not in tension with quality: a **shorter task file is also easier for the small model**, which gets lost in bulk. So the same discipline serves both goals.

- **A pointer beats a paste.** `src/auth/jwt.ts`, signature `signToken(userId: string): string` — ten tokens that fix the contract. Pasting the file costs hundreds and does the executor's job. Quote a snippet only when it's small and load-bearing.
- **Write telegraphically.** Fragments, not sentences. Signatures over prose. Don't restate the objective in three places or explain your reasoning in the generated files — the executor needs the *what*, not the *why*.
- **Split for correctness, not by reflex.** Each split duplicates context, so it costs tokens. Split when bundling risks the executor dropping a requirement (see principle 1); stop when a task is already one focused concern. Right-size beats max-split.

## Output structure

```
.opencode/plans/<plan-name>/
├── plan.md          # overview, decisions, conventions, task index
└── tasks/
    ├── task-01-<slug>.md
    └── ...
```

- `<plan-name>`: short kebab-case (e.g. `add-jwt-auth`). Task files zero-padded and slugged. All files in **English**.

## Workflow

1. **Explore first — never plan in the abstract.** Read the real files. Note exact paths, signatures, types, conventions (language, test/build/lint commands, layout, naming), and the seams where the change lands. Anything you don't pin down, the executor will guess — usually wrong. Every path/signature/command you write must be one you verified. If the request is ambiguous in a way that changes the plan, ask before writing.
2. **Name the plan, create `.opencode/plans/<plan-name>/tasks/`.**
3. **Write `plan.md`** (template below) — the architect's source of truth for ordering/decisions. Not required reading for the executor.
4. **Write the task files** (template below). Each is **self-contained**: executable from that one file alone. Add `Plan ref: plan.md § Task NN` as a fallback pointer, but never rely on the executor following it.
5. **Review pass — read each task as the small model.** "With no plan and no codebase knowledge, could I do exactly this and know when I'm done?" Fix what fails. This matters more than the first draft.
6. **Tell the user** the plan path, task count, and execution order. Offer to adjust granularity.

## Design principles for tasks

1. **One concern per task.** One module, one route/behaviour, or one tightly-coupled pair (impl + its test). The small model's typical failure isn't bad code — it's *dropping a requirement while juggling several*. "Add hashing AND a login route AND protect the list" is where it does two of three and silently skips one. So bundle only trivial changes that share the exact same context; otherwise one behaviour per task. Smaller tasks also give sharper verification — when something breaks you know which task.
2. **Self-contained.** Everything to execute goes in the task file: objective, minimal context, exact paths, contract, what to do (not paste-ready code), how to verify. Never needs the plan or a codebase tour.
3. **Contract, not implementation.** Pin the boundary exactly — paths, signatures, routes, types, schemas, commands — because the executor can't safely improvise these and they must match across tasks. Then stop: describe *what the code must do*, let it write the body. Signature + behaviour + constraints is the sweet spot.
4. **Verifiable.** Every task ends with a checkable Definition of Done and a concrete verify command. The executor wrote the code, not you — the verify step is how a weaker model catches its own mistakes. If the repo has no test infra yet, make bootstrapping it an early task, or verify with a command that already exists (build, a smoke run) — a Verify that fails for reasons outside the task reads as a false block.
5. **Explicit dependencies.** Each task lists prerequisites by ID and states what it can assume is already present.
6. **Right-sized.** Fits one focused pass of a limited window. If context or steps won't fit comfortably, split.
7. **`Files` is a concurrency contract.** The executor dispatches tasks with disjoint `Files` lists *in parallel* — an omitted file can put two subagents in the same file at once. List every file the task will create or modify, including easy-to-forget ones (barrel/index re-exports, config, migrations). Likewise, if the `Verify` step touches a shared resource (a dev server port, a database, the full test suite), declare it on the task's `Side effects` line so the dispatcher can keep colliding verifies in separate batches.

## The code-vs-spec dial

Default is **spec, not code**. Calibrate:

- **Always give (the contract):** exact paths; signatures, types, route shapes, schemas; inputs/outputs and status codes; error/edge behaviour; which existing pattern to match.
- **Give as hints:** which library/API and roughly how; the algorithm in prose; a 1–2 line snippet showing an existing pattern. Illustrative, not a full solution.
- **Let the executor write:** function bodies, wiring, boilerplate — whatever follows unambiguously from the contract.
- **Verbatim exception:** only a fragment that's genuinely tricky/security-sensitive with one correct form (a subtle type guard, a crypto call with specific params). Keep it to that fragment and say why. Pasting whole files means you're doing the executor's job.

Test: *could a competent coder implement this exactly one way from what I wrote?* Yes → stop. No → add contract detail, not implementation.

## When several tasks edit the same file

Splitting by concern often means 2–3 tasks touch the same file in sequence. By the time the executor opens task 3, tasks 1–2 already changed the file — the easiest way to feed it stale context. Guard against it:

- **Describe the file's state *after* the prerequisite tasks**, not the original (e.g. "after Task 02, `users.ts` imports `bcrypt` and defines `SALT_ROUNDS`").
- **Anchor the edit** relative to what's there ("add `/login` after `/register`, before `GET /`") so the executor doesn't clobber prior work.
- If keeping the "current state" in sync across three tasks gets fiddly, the split is too fine — merge those edits.

## `plan.md` template

```markdown
# Plan: <title>

## Goal
<1–3 sentences: what and why.>

## Current state
<Relevant existing code, its shape, where the change lands. Real paths.>

## Approach & key decisions
<Strategy and decisions the executor must respect — data shapes, patterns,
libraries, things to avoid. Bullets.>

## Conventions (every task)
- Language / framework: <...>
- Run tests / build / lint: `<commands>`
- Other: <naming, layout, error handling>

## Task index
| ID | Task | Depends on |
|----|------|-----------|
| 01 | <title> | — |
| 02 | <title> | 01 |

<!-- Progress lives in each task file's Status field — the single source of
truth. Don't duplicate it here: nothing updates plan.md during execution. -->

## Task 01 — <title>
<A few sentences on this task's slice — the fallback detail its task file points
back to. One chapter per task, so "§ Task NN" points at exactly one slice.>
```

## Task file template

Write it terse — fragments and signatures, not paragraphs. Omit any section that adds nothing for a given task (a task creating one file needs no "same-file" note).

````markdown
# Task 01 — <title>

- **ID:** 01 · **Depends on:** <IDs or none> · **Plan ref:** plan.md § Task 01 · **Status:** todo
- **Side effects:** <none, or the shared resources Verify touches: port 3000, test DB, full suite>

## Objective
<1 sentence.>

## Context
<Minimal slice to do THIS task alone: relevant signatures (quote only if small),
data shapes, what prior tasks produced that you rely on. If earlier tasks edited
this file, describe its state AFTER those edits.>

## Files
<Exhaustive — every file this task creates or modifies. The executor parallelizes
on disjoint Files, so a missing entry can cause two tasks to edit one file at once.>
- Create/Modify: `<path>` — <what changes>

## Contract
<The boundary to implement TO, not the implementation. Exact signatures, types,
routes, schemas, inputs/outputs, status codes. Code block for signatures. Behaviour
in prose. No function bodies.>

## What to do
<Instructions, not code: "hash with bcrypt (SALT_ROUNDS=10) before storing", "look
up by email, bcrypt.compare, 401 on mismatch". Name the API and the steps. A 1–2
line snippet ONLY to show a pattern to match. Fold in gotchas/constraints here —
edge cases, what NOT to touch, imports to reuse. A verbatim fragment goes here only
if genuinely tricky/security-sensitive; say why.>

## Definition of Done
- [ ] <checkable outcome>
- [ ] Verify command passes

## Verify
```bash
<exact command, e.g. npm test -- auth/jwt>
```
````

## Before you finish

- [ ] Each task is self-contained — no plan or codebase tour needed to execute.
- [ ] Contract specified, body left to the executor — no paste-ready implementations (bar a justified tricky fragment).
- [ ] Every path, signature, and command is real, not invented.
- [ ] One concern per task, right-sized for a limited window; splits justified by correctness, not reflex.
- [ ] `Files` exhaustive; `Side effects` declared wherever Verify touches a shared resource.
- [ ] Dependencies by ID; order consistent.
- [ ] Each task has a Definition of Done and a verify command.
- [ ] plan.md chapters map 1:1 to task files.
- [ ] Task files are terse — pointers over pastes, no restated rationale.
- [ ] User told the plan location and execution order.
