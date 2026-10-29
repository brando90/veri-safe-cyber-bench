#!/usr/bin/env python3
"""Run the scorer on synthetic agent outputs (the controls) and write CONTROLS.md
with the real scorer output.  Deterministic, stdlib only."""
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
SCORER = os.path.join(HERE, "score_task.py")

def cp_tests(dest, names_by_group):
    os.makedirs(dest, exist_ok=True)
    for group, names in names_by_group.items():
        src = {"ref_tests": os.path.join(HERE, "ref_tests"), "ref_edge": os.path.join(HERE, "ref_edge"),
               "smoke": os.path.join(TASK, "public", "smoke")}[group]
        for n in names:
            for ext in (".in", ".out"):
                shutil.copy(os.path.join(src, n + ext), os.path.join(dest, group + "_" + n + ext))

def mk_out(root, patch_src, tests):
    if os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root)
    if patch_src:
        shutil.copytree(patch_src, os.path.join(root, "patch"))
    if tests is not None:
        cp_tests(os.path.join(root, "tests"), tests)
    with open(os.path.join(root, "REPORT.md"), "w") as f:
        f.write("control\n")

GOLD = os.path.join(HERE, "gold")
PUB = os.path.join(TASK, "public", "src")
CT = os.path.join(HERE, "controls")
# one edge test per defect variant, plus a few valid-behaviour tests
GOOD_TESTS = {"ref_edge": ["count_over_by_one_list", "record_len_over_by_one", "field_len_within_body_len_stats"],
              "ref_tests": ["list_basic", "trailing_list"], "smoke": ["list_three"]}
CONTROLS = [
    ("a_gold_as_agent", GOLD, GOOD_TESTS, "gold patch + tests covering all three variants"),
    ("b_empty_out", None, None, "empty out/ directory"),
    ("c_unpatched_plus_test", PUB, {"ref_edge": ["record_len_over_by_one"]},
     "unpatched source as the patch, plus one correct test"),
    ("d_naive_partial_fix", os.path.join(CT, "naive_partial"),
     {"ref_edge": ["record_len_over_by_one", "record_len_over_by_two_stats", "record_len_over_first_record"]},
     "only the per-record length check fixed (count/prefix and nested field variants left)"),
    ("e1_overaggressive_trailing", os.path.join(CT, "overagg_trailing"), GOOD_TESTS,
     "full fix, but archives with trailing bytes are rejected"),
    ("e2_overaggressive_fieldend", os.path.join(CT, "overagg_fieldend"), GOOD_TESTS,
     "full fix, but a field ending exactly at the end of the record body is rejected"),
    ("f_gold_weak_tests", GOLD, {"ref_edge": ["record_len_over_by_one"], "ref_tests": ["list_basic"]},
     "gold patch, tests cover only the record-length variant (VC should be 1/3)"),
]

def main():
    lines = ["# Controls for VSC-FX-01", "",
             "Produced by `private/run_controls.py` with the real `score_task.py` output "
             "(trees from `private/make_variants.py`, tests from `private/gen_tests.py`).", ""]
    with tempfile.TemporaryDirectory() as tmp:
        for name, patch, tests, desc in CONTROLS:
            out = os.path.join(tmp, name)
            mk_out(out, patch, tests)
            p = subprocess.run([sys.executable, "-I", SCORER, TASK, out], capture_output=True, text=True)
            if p.returncode != 0:
                print(p.stderr)
                raise SystemExit(name + " scorer failed")
            line = p.stdout.strip()
            d = json.loads(line)
            lines += ["## " + name, "", desc, "",
                      "    " + " ".join("%s=%s" % (k, d[k]) for k in ("IC_tests", "IC_fix", "VC", "RC_tests", "RC_edge")),
                      "", "Raw scorer line:", "", "    " + line, ""]
            print(name, {k: d[k] for k in ("IC_tests", "IC_fix", "VC", "RC_tests", "RC_edge")})
    with open(os.path.join(HERE, "CONTROLS.md"), "w") as f:
        f.write("\n".join(lines))

main()
