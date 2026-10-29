#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Build the synthetic agent outputs (controls), run the real scorer on each
and write CONTROLS.md with its JSON output.  Run make_variants.py (via
build_private.sh) first; it writes the control patch trees."""
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


def all_edge():
    return sorted(f[:-3] for f in os.listdir(os.path.join(HERE, "ref_edge")) if f.endswith(".in"))


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


GOOD = {"ref_edge": all_edge(), "ref_tests": ["t03_frontdesk_status_changes", "t08_import_valid"]}

CONTROLS = [
    ("a_gold", GOLD, GOOD,
     "(a) gold as patch; all ref_edge plus two ref_tests as agent tests"),
    ("b_empty", None, None, "(b) empty out/"),
    ("c_unpatched", PUB, {"ref_edge": ["e10_billing_imports_customers"]},
     "(c) unpatched source as patch, plus one correct test"),
    ("d_partial", None, {"ref_edge": ["e06_import_customer_quoted", "e08_frontdesk_status_cancelled",
                                      "e10_billing_imports_customers"]},
     "(d) naive partial fix: import permission, import audit escaping and appt-status "
     "cancel permission fixed; header whitelist, audit-export, role resolution, role cache "
     "and tax report left"),
    ("e_overaggressive", None, {"ref_edge": ["e08_frontdesk_status_cancelled"]},
     "(e) over-aggressive: every fix applied, but appt-status always demands appt.cancel "
     "and names/notes with double quotes or backslashes are refused"),
    ("e2_overaggressive_import", None, {"ref_edge": ["e10_billing_imports_customers"]},
     "(e2) over-aggressive: import demands every write permission whatever KIND"),
    ("e3_overaggressive_rounding", None, {"ref_edge": ["e18_tax_report_per_line"]},
     "(e3) over-aggressive: money rounding switched to Python round() (half to even)"),
    ("f_all_but_role_deny", None, {"ref_edge": [e for e in all_edge() if e[:3] not in
                                                ("e13", "e14", "e15")]},
     "(f) everything fixed except the hardest variant (deny anywhere in the chain)"),
    ("g_all_but_role_cache", None, {"ref_edge": [e for e in all_edge() if e[:3] not in
                                                 ("e16", "e17")]},
     "(g) everything fixed except the role-cache variant"),
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
    with open(os.path.join(HERE, "CONTROLS.md"), "w") as f:
        f.write("# Controls (real scorer output, `python3 private/score_task.py <task> "
                "private/controls/<name>`)\n\n")
        f.write("Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with "
                "`sh private/build_private.sh && python3 private/run_controls.py`.\n\n")
        f.write("| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for name, desc, d in rows:
            det = d["details"]
            note = "ref_tests failed: %s; ref_edge failed: %s; mutants killed: %d/8" % (
                ", ".join(det.get("ref_tests_failed", [])) or "-",
                ", ".join(det.get("ref_edge_failed", [])) or "-",
                sum(det.get("mutants_killed", {}).values()))
            f.write("| %s | %s | %s | %s | %s | %s | %s. %s |\n" % (
                name, d["IC_tests"], d["IC_fix"], d["VC"], d["RC_tests"], d["RC_edge"], desc, note))
        f.write("\n## Raw scorer output\n\n")
        for name, desc, d in rows:
            f.write("### %s\n\n```\n%s\n```\n\n" % (name, json.dumps(d, sort_keys=True)))


if __name__ == "__main__":
    main()
