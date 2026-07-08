#!/usr/bin/env bash
# Run the behavior/quality benchmark for the local-agent skills, then aggregate
# each skill's runs into a benchmark.json/.md that the skill-creator eval-viewer
# can display.
#
# Usage:
#   bench/bench.sh [skill] [runs]
#     skill : planner | executor | reviewer | all   (default: all)
#     runs  : runs per configuration                (default: 3)
#
# Configure the model via env (see bench/config.example.env):
#   OLLAMA_URL   default http://localhost:11434/api/chat
#   BENCH_MODEL  default qwen2.5-coder:7b   (use "mock" to test the pipeline)
#   JUDGE_MODEL  default = BENCH_MODEL      (point at a stronger judge if you have one)
#
# Example:
#   OLLAMA_URL=http://localhost:11434/api/chat BENCH_MODEL=qwen2.5-coder:7b \
#     bench/bench.sh all 3
set -euo pipefail

SKILL="${1:-all}"
RUNS="${2:-3}"
BENCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$BENCH_DIR/.." && pwd)"
MODEL="${BENCH_MODEL:-qwen2.5-coder:7b}"
AGG="$REPO_ROOT/.claude/skills/skill-creator/scripts/aggregate_benchmark.py"

OUT="$BENCH_DIR/results/${MODEL//:/_}"
python "$BENCH_DIR/run_bench.py" --skill "$SKILL" --runs "$RUNS" --model "$MODEL" --out "$OUT"

if [ "$SKILL" = "all" ]; then
  SKILLS=(planner executor reviewer)
else
  SKILLS=("$SKILL")
fi

echo
echo "== Aggregating =="
for s in "${SKILLS[@]}"; do
  if [ -d "$OUT/$s" ]; then
    python "$AGG" "$OUT/$s" --skill-name "local-agent-$s" --skill-path "skills/local-agent-$s"
  fi
done

echo
echo "Done. To review results visually, open the eval-viewer against a benchmark.json:"
for s in "${SKILLS[@]}"; do
  echo "  $OUT/$s/benchmark.json"
done
echo "(eval-viewer lives at .claude/skills/skill-creator/eval-viewer/)"
