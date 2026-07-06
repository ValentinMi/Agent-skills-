# Task 04 — CI workflow validating skills and symlinks

- **ID:** 04 · **Depends on:** none · **Plan ref:** plan.md § Task 04 · **Status:** todo

## Objective
Add a GitHub Actions workflow that fails if any skill's frontmatter is invalid or any skill lacks its discovery symlink.

## Context
- Skills live in `.skills/<name>/` (each has a `SKILL.md`); Claude Code discovers them via symlinks `.claude/skills/<name>` → `../../.skills/<name>`.
- The repo ships its own validator: run **from inside `.skills/skill-creator/`** as `python -m scripts.quick_validate <path-to-skill>`; prints `Skill is valid!` and exits 0 on success, non-zero otherwise. Only third-party dep: `pyyaml`.
- There is no `.github/` directory yet.

## Files
- Create: `.github/workflows/validate-skills.yml`

## Contract
- Trigger: `push` and `pull_request` (all branches).
- One job, `ubuntu-latest`: checkout, set up Python 3.11, `pip install pyyaml`, then two checks (each a step, each must fail the job on any error):
  1. **Validate every skill**: for each directory `.skills/<name>/` containing a `SKILL.md`, run the validator from `.skills/skill-creator/` (i.e. `cd .skills/skill-creator && python -m scripts.quick_validate ../<name>`). Any failure → job fails.
  2. **Check symlinks**: for each such `.skills/<name>/`, `.claude/skills/<name>` must exist, be a symlink, and resolve to the source dir (compare `realpath .claude/skills/<name>` with `realpath .skills/<name>`). Any mismatch → job fails, printing the offending name.
- Loops must not hardcode skill names — new skills are picked up automatically.
- Bash steps must propagate failures (accumulate a failure flag or `exit 1` immediately; beware `for` loops swallowing non-zero statuses under default shell settings).

## What to do
Write the workflow. For step 1, iterate `for d in .skills/*/; do [ -f "$d/SKILL.md" ] || continue; ...` and call the validator with a path relative to `.skills/skill-creator/`. For step 2, compare realpaths and report each broken/missing symlink.

## Definition of Done
- [ ] Workflow file parses as YAML
- [ ] Both check-step scripts pass when run locally from the repo root
- [ ] A deliberately broken symlink makes the symlink script exit non-zero (test locally, then restore)
- [ ] Verify command passes

## Verify
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/validate-skills.yml'))" \
&& for d in .skills/*/; do n=$(basename "$d"); [ -f "$d/SKILL.md" ] || continue; \
     (cd .skills/skill-creator && python -m scripts.quick_validate "../$n") || exit 1; \
     [ "$(realpath ".claude/skills/$n")" = "$(realpath ".skills/$n")" ] || { echo "bad symlink: $n"; exit 1; }; \
   done && echo ALL-OK
```
