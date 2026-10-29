#!/bin/sh
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
# Deterministic rebuild of public/src, the mutants, the control trees, the
# smoke inputs and all .in/.out files (expected output comes from private/gold).
set -e
cd "$(dirname "$0")"
PATH="$HOME/envs/cc/bin:$PATH"
export PATH
rm -f gold/logpack
python3 -I make_variants.py
python3 -I gen_tests.py
