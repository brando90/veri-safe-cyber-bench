#!/bin/sh
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
# Deterministic rebuild of every generated artefact of VSC-FX-04:
#   public/src, private/gold, private/mutants/*, controls trees, expected .out files.
# usage: sh private/build_private.sh   (run from anywhere)
set -e
TASK="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="$HOME/envs/cc/bin:$PATH"
python3 -I "$TASK/private/tools/make_variants.py" "$TASK"
sh "$TASK/private/gold/build.sh"
for d in "$TASK/public/smoke" "$TASK/private/ref_tests" "$TASK/private/ref_edge"; do
  for f in "$d"/*.in; do
    "$TASK/private/gold/sesscache" < "$f" > "${f%.in}.out"
  done
done
# the solver tree must not ship a binary; neither need the others
find "$TASK" -name sesscache -type f -delete
echo "rebuilt $TASK"
