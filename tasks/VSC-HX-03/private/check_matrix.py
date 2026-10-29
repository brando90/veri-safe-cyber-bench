#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Author check: which hidden/smoke cases each tree (gold, original, mutants, controls) fails.

usage: python3 check_matrix.py [extra_tree...]
"""
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import score_task as st  # noqa: E402

TASK = os.path.dirname(HERE)
groups = {"smoke": st.cases(os.path.join(TASK, "public", "smoke")),
          "ref_tests": st.cases(os.path.join(HERE, "ref_tests")),
          "ref_edge": st.cases(os.path.join(HERE, "ref_edge"))}
trees = [("gold", os.path.join(HERE, "gold")), ("original", os.path.join(TASK, "public", "src"))]
trees += [(d, os.path.join(HERE, "mutants", d)) for d in sorted(os.listdir(os.path.join(HERE, "mutants")))]
trees += [(os.path.basename(p.rstrip("/")), p) for p in sys.argv[1:]]
with tempfile.TemporaryDirectory() as work:
    for label, src in trees:
        tree = st.build_tree(src, work)
        fails = {}
        t0 = time.time()
        for g, items in groups.items():
            fails[g] = [os.path.basename(c)[:-3].split("_")[0] for c in items
                        if not st.passes_exact(tree, c, 0)]
        print("%-36s %5.1fs smoke=%s tests=%s edge=%s" % (label, time.time() - t0, fails["smoke"],
                                                          fails["ref_tests"], fails["ref_edge"]))
