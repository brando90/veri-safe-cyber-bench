#!/bin/sh
# Deterministic rebuild of every generated artefact: public/src and mutants come
# from gold via make_variants.py; test inputs from gen_tests.py; expected outputs
# from gold via score_task.py --regen.
set -e
here="$(cd "$(dirname "$0")" && pwd)"
task="$(dirname "$here")"
python3 -B "$here/make_variants.py"
python3 -B "$here/gen_tests.py"
for tree in "$here/gold" "$task/public/src" "$here"/mutants/*; do
    sh "$tree/build.sh" >/dev/null
done
python3 -B "$here/score_task.py" --regen "$task"
