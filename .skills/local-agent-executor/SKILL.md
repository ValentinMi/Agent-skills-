---
name: local-agent-executor
description: Execute an implementation plan produced under .opencode/plans by working through its task files one at a time. Use this whenever the user wants to implement, run, or work through a plan or its tasks in .opencode/plans, do the next task, or continue where the last task left off. Built for a small local model with limited context and RAM — it loads only one task file at a time and never the whole plan, so the context stays light. Trigger on phrasing like "run the plan", "implement the tasks in .opencode/plans", "do the next task", "continue the plan", or "work through the task list".
---

# Local Agent Executor

You are executing a plan that another model already broke into a folder like `.opencode/plans/<name>/` with a `plan.md` and a `tasks/` directory. Your job is to implement those tasks — writing the actual code — **one at a time**.

Why one at a time matters: you have limited context and RAM. Loading the whole plan, or several task files at once, is exactly what overloads you and makes you slower and less accurate. The task files were written to be **self-sufficient** — each one carries the context it needs. Trust that, and keep your working memory to a single task.

## The loop

Repeat this for each task, from lowest number to highest:

1. **Find the next task.** In `tasks/`, files are numbered (`task-01-...`, `task-02-...`). Pick the lowest-numbered one whose `Status` is not `done`.
2. **Open only that one task file.** Read it fully — it is small by design.
3. **Do not open `plan.md` or any other task file.** Everything you need is in this task's `Context you need`, `Contract`, and `What to do`. Only if you are genuinely stuck, open the single section named in `Plan reference` — never the whole plan.
4. **Check `Depends on`.** Those tasks are already done and their code is on disk. If you need to see what they produced, open that specific **source file**, not its task file.
5. **Write the code** to satisfy the `Contract` and `What to do`. Respect `Constraints & gotchas`.
6. **Run the `Verify` command.** If it fails, fix it within this task and re-run until it passes.
7. **Mark the task done.** Tick the `Definition of Done` boxes and set the task's `Status` to `done`.
8. **Stop and reset.** Start the next task in a **fresh context** — don't carry this task's file or transcript forward.

## Keep your context light (the RAM rule)

- **One task = one clean context.** Between tasks, drop everything: the previous task file, its output, and the plan. Begin the next task fresh.
- **Never bulk-read** all the tasks or the whole `plan.md` "to get the big picture." The planner already distilled the big picture into each task's `Context you need`. Reading more just fills your memory and slows you down — it does not make the current task easier.
- **The source of truth for what already exists is the code on disk**, not your memory of earlier tasks. When in doubt, read the one relevant source file.
- If a task feels like it needs the whole plan, re-read its `Context you need` first — the answer is almost always there.

## Finding the next task without loading the plan

You do not need `plan.md` to know what to do next. List the task files and check their status, e.g.:

```bash
for f in .opencode/plans/*/tasks/task-*.md; do
  printf '%s  ' "$(grep -m1 -i 'Status' "$f")"; echo "$f"
done | sort
```

Take the first file that is not `done`.

## When something is off

- **Missing context:** open the one file the task points to (a specific source file, or the single `Plan reference` section) — nothing more.
- **The contract seems impossible or contradicts the code on disk:** stop and report it — name the task id and what is wrong — instead of guessing. A wrong build here gets inherited by every later task, so a small halt now is cheaper than a bad foundation.

## Running under OpenCode

Give each task its own run so context resets between tasks — that reset is the whole point. Finish a task (code written, verify passing, status set to `done`), then start the next task in a new session pointed at the same plan folder.
