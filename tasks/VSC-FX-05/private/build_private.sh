#!/bin/sh
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
# Deterministic rebuild: regenerates every .in (make_inputs.py) and every
# expected .out (public/smoke, ref_tests, ref_edge) by running the gold tree,
# then checks gold builds and that the original and each mutant differ from gold
# on at least one hidden case.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
task="$(dirname "$here")"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
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
echo "outputs regenerated from gold"
