# Task 05 — install-skills.sh: refuse to overwrite its own source

- **ID:** 05 · **Depends on:** none · **Plan ref:** plan.md § Task 05 · **Status:** todo

## Objective
Make `install-skills.sh` refuse to install when the destination resolves to the source, instead of rsyncing `.skills/<name>/` onto itself through a symlink.

## Context
`install-skills.sh` (repo root, bash, `set -euo pipefail`) mirrors `$SKILLS_SRC/<name>/` (`SKILLS_SRC="$SCRIPT_DIR/.skills"`) into `$TARGET_DIR/<name>/` via `rsync -a --delete` or an `rm -rf` + `cp -a` fallback. In this repo `.claude/skills/<name>` is a symlink to `../../.skills/<name>`, so `./install-skills.sh .claude/skills` currently writes each skill onto its own source (and the fallback path `rm -rf`s the symlink). The script already: normalizes `TARGET_DIR` to an absolute path (~line 48), tracks per-skill failures with a `failed` counter and `✗ ... (skipped)` messages (~lines 72–76), and exits non-zero via `[ "$failed" -eq 0 ]` (last line).

## Files
- Modify: `install-skills.sh` — one global check after TARGET_DIR normalization; one per-skill check inside the install loop

## Contract
1. Global check, right after `TARGET_DIR` is normalized: if `TARGET_DIR` resolves to the same directory as `$SKILLS_SRC` (compare with `realpath`), print an error naming both paths to stderr and `exit 1`.
2. Per-skill check, in the loop after the existing `SKILL.md` existence check: if `$dst` exists and `realpath "$dst"` equals `realpath "$src"`, print `  ✗ <name> — target resolves to source (symlink?), skipped` to stderr, increment `failed`, `continue`. Must run before any `rsync`/`rm` touches `$dst`.
3. Behaviour otherwise unchanged: normal installs into a fresh or unrelated directory work exactly as before; a run with any skipped skill still exits non-zero (existing `failed` mechanism).
4. Match the script's existing style (same message format, `>&2` for errors).

## What to do
Add the two checks. Use `realpath` (available where rsync/cp are); guard the per-skill call with `[ -e "$dst" ]` since `realpath` on a missing path can fail under `set -e`.

## Definition of Done
- [ ] `./install-skills.sh .claude/skills` exits non-zero, installs nothing, and the symlinks in `.claude/skills/` are intact afterwards
- [ ] `./install-skills.sh .skills` exits non-zero immediately (global check)
- [ ] Install into a scratch dir still works and exits 0
- [ ] Verify command passes

## Verify
```bash
! ./install-skills.sh .claude/skills \
&& [ -L .claude/skills/local-agent-planner ] \
&& ! ./install-skills.sh .skills \
&& t=$(mktemp -d) && ./install-skills.sh "$t" local-agent-planner \
&& [ -f "$t/local-agent-planner/SKILL.md" ] && rm -rf "$t" && echo OK
```
