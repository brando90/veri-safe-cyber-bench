#!/bin/sh
# Deterministic rebuild of everything private: builds the original, gold and
# mutants into private/build/<name>/, regenerates ref_tests/ref_edge inputs and
# expected outputs from gold (cross-checked against an independent Python model),
# and regenerates public/smoke expected outputs.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
export PATH="$HOME/envs/cc/bin:$PATH"
rm -rf "$HERE/build"
mkdir -p "$HERE/build"
cp -r "$HERE/../public/src" "$HERE/build/original"
cp -r "$HERE/gold" "$HERE/build/gold"
for m in "$HERE"/mutants/*/; do
    cp -r "$m" "$HERE/build/$(basename "$m")"
done
for d in "$HERE"/build/*/; do
    rm -f "$d/tilekit"
    sh "$d/build.sh"
done
python3 -I "$HERE/gen_tests.py" "$HERE"
echo "build_private: ok"
