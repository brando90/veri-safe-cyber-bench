#!/usr/bin/env bash
# Copy this repo into anarres-organization/anarres at experiments/cyber/veri-safe-cyber-bench/ and push.
# Run from a machine whose git is signed in to GitHub with write access to the Anarres org (e.g. as brando90 after accepting the invite).
# Usage: tools/push_to_anarres.sh [--pr]   (--pr pushes a branch and opens a pull request instead of pushing main)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"
git clone --depth 1 https://github.com/anarres-organization/anarres.git "$WORK/anarres"
DEST="$WORK/anarres/experiments/cyber/veri-safe-cyber-bench"
mkdir -p "$DEST"
rsync -a --exclude .git "$SRC"/ "$DEST"/
rm -f "$DEST/tools/push_to_anarres.sh"
cd "$WORK/anarres"
git add experiments/cyber/veri-safe-cyber-bench
git commit -m "cyber: add veri-safe-cyber-bench defensive find-and-fix tasks"
if [ "${1:-}" = "--pr" ]; then
  git checkout -b cyber/veri-safe-cyber-bench && git push -u origin HEAD && gh pr create --fill
else
  git push origin HEAD:main
fi
