#!/bin/sh
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-30.
# Deterministic rebuild of everything derived: gold (gen_gold.py), public/src, the
# mutants and the control patch trees (make_variants.py), every .in file
# (make_inputs.py) and every expected .out file (public/smoke, ref_tests,
# ref_edge), the latter by running the gold tree in a fresh empty directory.
# Then run check_variants.py, check_decoys.py and run_controls.py (writes CONTROLS.md).
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
task="$(dirname "$here")"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 LC_ALL=C.UTF-8
python3 "$here/gen_gold.py" > /dev/null
python3 "$here/make_variants.py"
python3 "$here/make_inputs.py"
cp -r "$here/gold" "$work/gold"
sh "$work/gold/build.sh"
for dir in "$task/public/smoke" "$here/ref_tests" "$here/ref_edge"; do
  for f in "$dir"/*.in; do
    mkdir "$work/cwd"
    (cd "$work/cwd" && python3 "$work/gold/main.py" < "$f" > "${f%.in}.out")
    rmdir "$work/cwd"
  done
done
find "$task" -name __pycache__ -type d -prune -exec rm -rf {} +
echo "outputs regenerated from gold"
