#!/bin/sh
# Deterministic rebuild of every generated artefact: expected outputs come from gold.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
task="$(dirname "$here")"
for tree in "$here/gold" "$task/public/src" "$here"/mutants/*; do
    sh "$tree/build.sh" >/dev/null
done
python3 -B "$here/score_task.py" --regen "$task"
