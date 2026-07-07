---
name: local-agent-executor
description: Execute an implementation plan produced under .opencode/plans by dispatching its task files to subagents — one task per subagent, independent tasks in parallel (with a strict concurrency cap tuned for a local model). Use this whenever the user wants to implement, run, or work through a plan or its tasks in .opencode/plans, do the next task, run tasks in parallel, or continue where the last task left off. Built for a small local model with limited context and RAM — the dispatcher reads only task headers and each subagent loads only its one task file, never the whole plan. Trigger on phrasing like "run the plan", "implement the tasks in .opencode/plans", "do the next task", "run the tasks in parallel", "continue the plan", or "work through the task list".
---

# Local Agent Executor

You are executing a plan that another model already broke into a folder like `.opencode/plans/<name>/` with a `plan.md` and a `tasks/` directory. Your job is to get those tasks implemented — but **not in your own context**.

You act as the **dispatcher**: for every task you launch a **subagent** whose entire world is that one task file, and when several tasks are independent you launch their subagents **in parallel**. This is how a small model with limited context and RAM stays fast *and* accurate: each task gets a fresh, empty context (no leftover transcript to confuse it), and independent tasks don't wait on each other. The task files were written to be **self-sufficient** — each one carries the context it needs. Trust that.

## The dispatch loop

Repeat until every task is `done`:

1. **Scan headers only.** For each `tasks/task-*.md`, read just the metadata line (`ID`, `Depends on`, `Status`) and the `Files` list. **Never read task bodies, `plan.md`, or task output in the dispatcher** — your context must stay near-empty so you can run the whole plan without resetting.
2. **Find the ready tasks.** A task is *ready* when its `Status` is `todo` and every ID in `Depends on` is `done`.
3. **Build a parallel batch.** From the ready tasks, keep only those whose `Files` lists are **pairwise disjoint** — two tasks that touch the same file never run at the same time. Cap the batch size (see the performance rules below).
4. **Launch one subagent per task in the batch, in parallel.** Each subagent's instructions: "Execute `.opencode/plans/<plan-name>/tasks/task-NN-<slug>.md` following the 'What each subagent does' steps. Read only that file plus the source files it names. Report done or blocked, in one or two sentences."
5. **Wait for the whole batch to finish.** Read only each subagent's short final report — not its transcript. Completions unlock new tasks, so go back to step 1 and re-scan.
6. **If a subagent reports blocked or its verify failed**, do not dispatch anything that depends on that task. Surface the task ID and the reported problem to the user; keep dispatching independent branches if any remain.

## Performance rules — read before parallelizing

Parallel subagents are only a win if the machine can actually serve them. On a local backend, every concurrent subagent is **another inference stream against the same model**: each one gets its own KV cache, so RAM/VRAM cost multiplies per slot, and if the server isn't configured for concurrent requests (e.g. Ollama's `OLLAMA_NUM_PARALLEL`, default low) the extra subagents just **queue** — you pay orchestration overhead for zero speedup.

- **Default cap: 2 subagents in parallel. Never exceed 3**, even if more tasks are ready — the leftover ready tasks simply go in the next batch.
- **Drop to 1 (sequential) when:** the machine is RAM/VRAM-tight, tasks look heavy (large `Files` lists, big contracts), the backend is known to serialize requests, or you're unsure. Sequential-through-subagents keeps the main benefit — a fresh context per task — and a correct sequential run always beats a thrashing parallel one.
- **Serialize on shared side effects.** Even with disjoint `Files`, two `Verify` commands can collide — a dev server on the same port, the same database, the full test suite writing shared artifacts. If two ready tasks' verify steps could interfere, put them in different batches.
- **Don't shrink batches to 1 task "to be safe" when tasks are small and independent** — two light, disjoint tasks in parallel is the sweet spot this skill aims for.

## What each subagent does (one task, start to finish)

1. **Open only your one task file.** Read it fully — it is small by design.
2. **Do not open `plan.md` or any other task file.** Everything you need is in this task's `Context`, `Contract`, and `What to do`. Only if you are genuinely stuck, open the single section named in `Plan ref` — never the whole plan.
3. **Check `Depends on`.** Those tasks are already done and their code is on disk. If you need to see what they produced, open that specific **source file**, not its task file.
4. **Write the code** to satisfy the `Contract` and `What to do`. Respect the constraints and gotchas folded into `What to do`.
5. **Run the `Verify` command.** If it fails, fix it within this task and re-run until it passes.
6. **Mark the task done.** If the workflow uses `local-agent-reviewer`, request its review of this task's diff first — only mark `done` on an **APPROVE** verdict; on **CHANGES NEEDED**, apply the fixes, re-run `Verify`, and get re-reviewed. Otherwise, tick the `Definition of Done` boxes and set the task's `Status` to `done` directly.
7. **Report back in one or two sentences** — "task NN done, verify passing" or "task NN blocked: <why>". Never paste your transcript or the code into the report; the dispatcher must stay light.

## Keep your context light (the RAM rule)

- **Dispatcher reads headers, subagents read one task.** No context in the system ever holds more than one task body.
- **Never bulk-read** all the tasks or the whole `plan.md` "to get the big picture." The planner already distilled the big picture into each task's `Context`. Reading more just fills your memory and slows you down — it does not make the current task easier.
- **The source of truth for what already exists is the code on disk**, not your memory of earlier tasks or batches. When in doubt, a subagent reads the one relevant source file.
- If a task feels like it needs the whole plan, re-read its `Context` first — the answer is almost always there.

## Scanning headers without loading the plan

You do not need `plan.md` to know what is ready. List the task files of the plan you're executing (`<plan-name>` is that plan's folder) and pull just the metadata, e.g.:

```bash
for f in .opencode/plans/<plan-name>/tasks/task-*.md; do
  printf '%s | %s | %s\n' "$f" \
    "$(grep -m1 -i 'Status' "$f")" \
    "$(grep -m1 -i 'Depends on' "$f")"
done
```

Cross-check `Depends on` IDs against the statuses you just listed; dispatch every `todo` task whose dependencies are all `done`, batched by the rules above.

## When something is off

- **Missing context (in a subagent):** open the one file the task points to (a specific source file, or the single `Plan ref` section) — nothing more.
- **The contract seems impossible or contradicts the code on disk:** the subagent stops and reports it — task ID plus what is wrong — instead of guessing; the dispatcher relays it to the user and freezes that dependency branch. A wrong build here gets inherited by every later task, so a small halt now is cheaper than a bad foundation.

## Running under OpenCode

Use OpenCode's subagent/task mechanism to give each task its own isolated run — that isolation is the whole point, and launching several at once is what makes independent tasks parallel. If your setup has no subagent capability, fall back to the sequential mode: finish one task per session (code written, verify passing, status `done`), then start the next task in a **new session** pointed at the same plan folder — never carry one task's transcript into the next.
