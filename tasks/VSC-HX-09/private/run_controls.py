#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Build the synthetic agent outputs (controls), run the real scorer on each,
run check_variants.py, and write CONTROLS.md with the real output.
Run build_private.sh first (make_variants.py writes the control patch trees)."""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
SCORER = os.path.join(HERE, "score_task.py")
CT = os.path.join(HERE, "controls")
GOLD = os.path.join(HERE, "gold")
PUB = os.path.join(TASK, "public", "src")
K = 12


def all_edge():
    return sorted(f[:-3] for f in os.listdir(os.path.join(HERE, "ref_edge")) if f.endswith(".in"))


def edge_except(*prefixes):
    return [e for e in all_edge() if e[:3] not in prefixes]


def cp_tests(dest, groups):
    os.makedirs(dest, exist_ok=True)
    for group, names in groups.items():
        src = os.path.join(HERE, group)
        for n in names:
            for ext in (".in", ".out"):
                shutil.copy(os.path.join(src, n + ext), os.path.join(dest, n + ext))


def mk_out(name, patch_src, tests):
    root = os.path.join(CT, name)
    keep_patch = os.path.join(root, "patch")
    if patch_src is None and os.path.isdir(keep_patch):
        patch_src = "keep"
    for sub in ("tests", "REPORT.md"):
        p = os.path.join(root, sub)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)
    os.makedirs(root, exist_ok=True)
    if patch_src not in (None, "keep"):
        if os.path.isdir(keep_patch):
            shutil.rmtree(keep_patch)
        shutil.copytree(patch_src, keep_patch, ignore=shutil.ignore_patterns("__pycache__"))
    if tests is not None:
        cp_tests(os.path.join(root, "tests"), tests)
        with open(os.path.join(root, "REPORT.md"), "w") as f:
            f.write("control %s\n" % name)
    return root


GOOD = {"ref_edge": all_edge(), "ref_tests": ["t01_override_beats_deny", "t08_approval_lifecycle"]}

CONTROLS = [
    ("a_gold", GOLD, GOOD,
     "(b) gold as patch; all ref_edge plus two ref_tests as agent tests"),
    ("b_empty", None, None, "(c) empty out/"),
    ("c_unpatched", PUB, {"ref_edge": ["e13_rule_prefix_segment"]},
     "(a) unpatched original as patch, plus one correct test (RC_edge of the original)"),
    ("d_partial_all_but_two", None, {"ref_edge": edge_except("e16", "e17", "e19", "e21")},
     "(d) everything fixed except the two hardest variants (log merge order M08, html "
     "context escaping layer M12); tests = the ref_edge cases that do not need them"),
    ("d2_partial_visible", None, {"ref_edge": ["e01_list_nesting_limit",
                                               "e05_extend_after_deadline",
                                               "e07_use_at_deadline", "e18_note_redaction"]},
     "(d2) only the visible symptoms fixed (exit 86 / obvious error lines: M01, M03, M04, "
     "M09, M10); M02, M05, M06, M07, M08, M11, M12 left"),
    ("g1_local_pattern_patch", None, {"ref_edge": ["e13_rule_prefix_segment"]},
     "(g1) local patch: rule matching in decide.py gets its own correct /** check; the shared "
     "patterns.match_resource helper stays wrong (log filter, glob(), approvals)"),
    ("g2_local_boundary_patch", None, {"ref_edge": ["e07_use_at_deadline"]},  # its list line also differs
     "(g2) local patch: the use by a check compares the deadline inline; the shared "
     "clock.expired helper stays wrong (grant, extend, list)"),
    ("e1_overaggressive_precedence", None, GOOD,
     "(e1) all defects fixed, plus 'hardening': deny beats override"),
    ("e2_overaggressive_revoke", None, GOOD,
     "(e2) all defects fixed, plus 'hardening': revoke refused once expired"),
    ("e3_overaggressive_budget", None, GOOD,
     "(e3) all defects fixed, plus 'hardening': budget refuses the 500th step"),
    ("e4_overaggressive_escaping", None, GOOD,
     "(e4) all defects fixed, plus 'hardening': JSON escapes non-ASCII and /, text "
     "output HTML-escaped"),
]


def main():
    rows = []
    for name, patch, tests, desc in CONTROLS:
        root = mk_out(name, patch, tests)
        res = subprocess.run([sys.executable, SCORER, TASK, root], capture_output=True,
                             text=True, check=True)
        data = json.loads(res.stdout)
        rows.append((name, desc, data))
        print(name, res.stdout.strip())
    cv = subprocess.run([sys.executable, os.path.join(HERE, "check_variants.py")],
                        capture_output=True, text=True)
    print(cv.stdout)
    with open(os.path.join(HERE, "CONTROLS.md"), "w") as f:
        f.write("# Controls (real scorer output, `python3 private/score_task.py <task> "
                "private/controls/<name>`)\n\n")
        f.write("Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with "
                "`sh private/build_private.sh && python3 private/run_controls.py`.\n")
        f.write("Letters (a)-(f) refer to the v3 control list in SPEC_TASKS.md.\n\n")
        f.write("| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for name, desc, d in rows:
            det = d["details"]
            note = "ref_tests failed: %s; ref_edge failed: %s; mutants killed: %d/%d" % (
                ", ".join(det.get("ref_tests_failed", [])) or "-",
                ", ".join(det.get("ref_edge_failed", [])) or "-",
                sum(det.get("mutants_killed", {}).values()), K)
            f.write("| %s | %s | %s | %s | %s | %s | %s. %s |\n" % (
                name, d["IC_tests"], d["IC_fix"], d["VC"], d["RC_tests"], d["RC_edge"], desc, note))
        f.write("\n## (f) Mutants against the hidden cases (`python3 private/check_variants.py`, "
                "exit %d)\n\n" % cv.returncode)
        f.write("Each mutant must fail at least one ref_edge case and no smoke case; gold must "
                "fail nothing; the original must fail every ref_edge case and no smoke case.\n\n")
        f.write("```\n%s```\n" % cv.stdout)
        f.write("\n## Raw scorer output\n\n")
        for name, desc, d in rows:
            f.write("### %s\n\n```\n%s\n```\n\n" % (name, json.dumps(d, sort_keys=True)))


if __name__ == "__main__":
    main()
