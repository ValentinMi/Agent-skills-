---
name: local-agent-reviewer
description: Review the code a single task produced against that task's own spec before it is marked done, in the .opencode/plans planner/executor workflow. Use this whenever the user wants to review, check, or verify the work of a task, review a diff before marking it done, or gate a task in a plan under .opencode/plans. Built for a small local model with limited context — it reviews only the current task's diff against that one task file, never the whole plan or other tasks, and returns an APPROVE or CHANGES NEEDED verdict. Trigger on phrasing like "review this task", "check the diff before marking done", "did this task actually meet its spec", or "review the changes for task 03".
---

# Local Agent Reviewer

You are reviewing the code that one task produced, against that task's own spec, before it gets marked `done`. This is the gate between "code written + verify passed" and "move to the next task."

Why it matters: the `Verify` command proves the code *runs*; it does not prove the code is *correct and complete versus what the task asked for*. A task can pass a thin verify yet miss a Definition-of-Done item, break a constraint, or drift outside its scope. Because every later task builds on this one, a wrong result here is inherited by everything after it — so catching it now is far cheaper than later.

Keep it light: review **only the current task's diff against its one task file**. Do not open `plan.md` or other task files — that is not needed to judge whether this task met its own spec, and it just fills your context.

## What to review

1. **Get the diff** for this task — the code that changed since the task started, **scoped to the paths in the task's `Files` section**:
   ```bash
   git diff -- <paths from Files>            # unstaged changes, this task only
   git diff HEAD~1 -- <paths from Files>     # or vs the prior commit, if committed per task
   ```
   Always scope: the executor may run other tasks in parallel, so the raw
   working-tree diff can contain *another* task's in-flight changes — an unscoped
   diff judges this task on someone else's code. (Changes to files *outside* the
   task's `Files` are still findable: `git diff --stat` names them without loading
   their content — see the scope-creep check.)
   If there is no git, compare the files the task's `Files` section named against what the task asked for.
2. **Read the task file's** `Contract`, `What to do` (constraints and gotchas are folded in there), and `Definition of Done`. That is your rubric — nothing else.

## Checklist (all against the task's own spec)

- **Contract met exactly** — signatures, types, routes, schemas, status codes match what the task specified. No renamed or missing exports.
- **Every Definition of Done item is truly satisfied** — verified against the actual code, not just because a box is ticked. Tick-without-truth is the most common failure.
- **Constraints respected** — the gotchas folded into `What to do`: things the task said to match, reuse, or not touch.
- **No scope creep** — the diff changes what this task owns and nothing else. Check `git diff --stat` for changed files beyond the task's `Files` paths. Caveat under parallel execution: an extra file may be *another* in-flight task's legitimate work — if the change is clearly part of this task's feature, it's scope creep (reject); if it looks like a separate concern, report it as an unattributed change for the dispatcher to sort out instead of blocking this task on it.
- **Verify genuinely passed** — re-run the task's `Verify` command if unsure; a claimed pass with no evidence doesn't count.
- **No obvious correctness bugs** in the changed lines — off-by-one, wrong error paths, leaked secrets, unhandled cases the task called out.

## Verdict

End with one of two clear outcomes:

- **APPROVE** — the task meets its spec. Say so plainly; the task can be marked `done`.
- **CHANGES NEEDED** — list concrete, minimal fixes, each tied to a spec item (e.g. "DoD #2 unmet: `/login` returns 200 with no token on bad password; should be 401"). Hand these back to the executor to fix, then review again. Keep the list short and actionable — don't rewrite the code yourself, and don't pile on style opinions the task never asked for.

If the same task comes back still failing after **two fix rounds**, stop the loop: flag the task for a human (or the planner) with your remaining findings. Non-convergence at that point is a spec or capability problem, not a polish problem — a third round just burns the machine.

## When the spec itself looks wrong

If the code is faithful to the task but the **task's own spec** seems wrong or contradicts the code already on disk, that is not a code fix — flag it (name the task id and the conflict) for the planner or a human. Don't force the code to satisfy a broken spec; that just launders the error forward.

## Keep your context light

- One task's diff + one task file. Nothing else.
- Don't read the plan or other tasks "for context" — the task file is the whole rubric. Reading more spends memory you need for judging the actual lines that changed.
