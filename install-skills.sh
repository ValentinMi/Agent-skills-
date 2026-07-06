#!/usr/bin/env bash
#
# install-skills.sh — install or update this repo's skills into a target folder.
#
# Copies each skill from skills/<name>/ into <target-dir>/<name>/. Running it
# again updates an existing install (each skill folder is mirrored exactly, so
# files removed from a skill are also removed from the target). __pycache__ and
# *.pyc are never copied.
#
# Usage:
#   ./install-skills.sh <target-skills-dir> [skill-name ...]
#
# Examples:
#   ./install-skills.sh ~/.config/opencode/skills           # all skills
#   ./install-skills.sh ../my-project/.claude/skills          # all skills
#   ./install-skills.sh ~/.config/opencode/skills local-agent-executor
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"

usage() {
  # Print the comment header (everything after the shebang up to the first
  # non-comment line), stripping the leading "# ".
  awk 'NR==1{next} /^#/{sub(/^# ?/,""); print; next} {exit}' "${BASH_SOURCE[0]}"
  exit "${1:-0}"
}

[ $# -ge 1 ] || { echo "error: missing <target-skills-dir>" >&2; echo >&2; usage 1 >&2; }
case "$1" in -h|--help) usage 0 ;; esac

TARGET_DIR="$1"; shift
[ -d "$SKILLS_SRC" ] || { echo "error: source skills dir not found: $SKILLS_SRC" >&2; exit 1; }

# Determine which skills to install: the named ones, or every skill in skills/.
declare -a SKILLS=()
if [ $# -gt 0 ]; then
  SKILLS=("$@")
else
  for d in "$SKILLS_SRC"/*/; do
    [ -f "${d}SKILL.md" ] && SKILLS+=("$(basename "$d")")
  done
fi
[ ${#SKILLS[@]} -gt 0 ] || { echo "error: no skills found to install" >&2; exit 1; }

mkdir -p "$TARGET_DIR"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"  # normalize to absolute

if [ "$(realpath "$TARGET_DIR")" = "$(realpath "$SKILLS_SRC")" ]; then
  echo "error: target dir ($TARGET_DIR) is the skills source dir ($SKILLS_SRC) — refusing to install onto itself" >&2
  exit 1
fi

have_rsync=0; command -v rsync >/dev/null 2>&1 && have_rsync=1

sync_one() {
  local src="$1" dst="$2"
  if [ "$have_rsync" -eq 1 ]; then
    rsync -a --delete \
      --exclude='__pycache__/' --exclude='*.pyc' \
      "$src/" "$dst/"
  else
    rm -rf "$dst"
    mkdir -p "$dst"
    cp -a "$src/." "$dst/"
    find "$dst" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
    find "$dst" -name '*.pyc' -type f -delete 2>/dev/null || true
  fi
}

echo "Installing skills into: $TARGET_DIR"
installed=0; updated=0; failed=0
for name in "${SKILLS[@]}"; do
  src="$SKILLS_SRC/$name"
  dst="$TARGET_DIR/$name"
  if [ ! -f "$src/SKILL.md" ]; then
    echo "  ✗ $name — not found in $SKILLS_SRC (skipped)" >&2
    failed=$((failed + 1))
    continue
  fi
  if [ -e "$dst" ] && [ "$(realpath "$dst")" = "$(realpath "$src")" ]; then
    echo "  ✗ $name — target resolves to source (symlink?), skipped" >&2
    failed=$((failed + 1))
    continue
  fi
  if [ -e "$dst" ]; then action="updated"; updated=$((updated + 1))
  else action="installed"; installed=$((installed + 1)); fi
  sync_one "$src" "$dst"
  echo "  ✓ $name — $action"
done

echo "Done: $installed installed, $updated updated, $failed skipped."
[ "$failed" -eq 0 ]
