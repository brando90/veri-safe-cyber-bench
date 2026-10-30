#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Sanity check of the hidden cases against the original and the mutants.

usage: python3 check_variants.py [-v]
Prints, for public/src, gold and every mutant, which smoke / ref_tests /
ref_edge cases fail.  Exits 1 if gold fails anything, if a mutant fails no
hidden case, if the original fails a smoke case, or if a ref_edge case passes
on the original.
"""
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
import score_task  # noqa: E402


def failing(tree_src, groups):
    with tempfile.TemporaryDirectory() as tmp:
        tree, ok, msg = score_task.build(tree_src, pathlib.Path(tmp))
        if not ok:
            return None
        out = {}
        for gname, cases in groups.items():
            out[gname] = sorted(n for n, i, o in cases if not score_task.run_case(tree, i, o))
        return out


def main():
    groups = {
        "smoke": score_task.cases(TASK / "public" / "smoke"),
        "ref_tests": score_task.cases(HERE / "ref_tests"),
        "ref_edge": score_task.cases(HERE / "ref_edge"),
    }
    bad = False
    trees = [("gold", HERE / "gold"), ("original", TASK / "public" / "src")]
    trees += [(p.name, p) for p in sorted((HERE / "mutants").iterdir())]
    for name, src in trees:
        res = failing(src, groups)
        if res is None:
            print("%-18s BUILD FAILED" % name)
            bad = True
            continue
        print("%-18s smoke=%s ref_tests=%s ref_edge=%s" % (name, res["smoke"], res["ref_tests"],
                                                          res["ref_edge"]))
        if name == "gold" and any(res.values()):
            bad = True
        if name == "original":
            edge_pass = sorted(set(n for n, _, _ in groups["ref_edge"]) - set(res["ref_edge"]))
            if res["smoke"] or edge_pass:
                print("   original passes ref_edge:", edge_pass)
                bad = True
        if name.startswith("M") and not (res["ref_tests"] or res["ref_edge"]):
            print("   mutant not killed by any hidden case")
            bad = True
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
