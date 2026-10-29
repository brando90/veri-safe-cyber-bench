#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Dev helper: run one or more NAME.in files against a source tree and show the result.

usage: python3 run_case.py <src_tree> NAME.in...
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_task  # noqa: E402

tree = sys.argv[1]
for path in sys.argv[2:]:
    res = score_task.run_case(tree, path)
    print("=== %s  code=%s error=%s" % (os.path.basename(path), res["code"], res["error"]))
    if res["stdout"] is not None:
        sys.stdout.write(res["stdout"].decode("utf-8", "replace"))
    if res["stderr"]:
        print("--- stderr\n" + res["stderr"])
