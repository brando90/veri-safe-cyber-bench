#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Build the synthetic agent outputs (controls), run the real scorer on each
and write CONTROLS.md with its JSON output, followed by the output of
check_variants.py (control f: every mutant is caught by a ref_edge case and
by no smoke case).  Run build_private.sh first; make_variants.py writes the
control patch trees."""
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
MUT = os.path.join(HERE, "mutants")


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


CONTROLS = [
    ("a_gold", GOLD, {"ref_edge": all_edge(), "ref_tests": ["t07_rounding_half_up", "t24_rounding_reports"]},
     "(a) gold as patch; all ref_edge plus two ref_tests as agent tests"),
    ("b_empty", None, None, "(b) empty out/"),
    ("c_unpatched", PUB, {"ref_edge": ["e15_invoice_total"]},
     "(c) unpatched source as patch, plus one correct test"),
    ("d_partial", None, {"ref_edge": edge_except("e01", "e02", "e03", "e04", "e13")},
     "(d) partial fix: ten variants fixed; retry place (M01) and sender turn stamp (M02) left; "
     "agent tests = the ref_edge cases that pass on this patch"),
    ("d2_local_patches", None, {"ref_edge": ["e08_busy_hint_seconds", "e09_volume_exact_kib",
                                             "e10_batch_capacity", "e11_batch_full_recipient",
                                             "e17_direct_respects_limits", "e18_direct_hourly"]},
     "(d2) naive fix: busy units, KiB, batch capacity, reassembly dup and direct limits fixed; "
     "window edge and money total patched only at the visible caller (dedup.find, invoice "
     "total) instead of the shared helper; ordering/state/TTL/dedup-remember defects left"),
    ("e1_overaggressive_quiet_dedup", None, {"ref_edge": ["e14_rejected_not_remembered"]},
     "(e1) over-aggressive on top of the full fix: urgent also held by quiet hours, and a "
     "duplicate refreshes the dedup window"),
    ("e2_overaggressive_rounding", None, {"ref_edge": ["e15_invoice_total"]},
     "(e2) over-aggressive on top of the full fix: cents() via Python round() (half to even)"),
    ("e3_overaggressive_limits", None, {"ref_edge": ["e17_direct_respects_limits"]},
     "(e3) over-aggressive on top of the full fix: limits also hold back fragments of "
     "messages that already started"),
    ("g_all_but_turn", os.path.join(MUT, "M02_turn_stamp"), {"ref_edge": edge_except("e03", "e04")},
     "(g) everything fixed except the sender turn stamp (M02)"),
]


def main():
    rows = []
    for name, patch, tests, desc in CONTROLS:
        root = mk_out(name, patch, tests)
        res = subprocess.run([sys.executable, SCORER, TASK, root], capture_output=True,
                             text=True, check=True)
        data = json.loads(res.stdout)
        rows.append((name, desc, data))
        print(name, res.stdout.strip(), flush=True)
    cv = subprocess.run([sys.executable, os.path.join(HERE, "check_variants.py")],
                        capture_output=True, text=True)
    print(cv.stdout, "check_variants exit=%d" % cv.returncode)
    n_mut = len([d for d in os.listdir(MUT) if os.path.isdir(os.path.join(MUT, d))])
    with open(os.path.join(HERE, "CONTROLS.md"), "w") as f:
        f.write("# Controls (real scorer output, `python3 private/score_task.py <task> "
                "private/controls/<name>`)\n\n")
        f.write("Factor order: IC_tests, IC_fix, VC, RC_tests, RC_edge. Regenerate with "
                "`sh private/build_private.sh && python3 private/run_controls.py`.\n\n")
        f.write("| Control | IC_tests | IC_fix | VC | RC_tests | RC_edge | Notes |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for name, desc, d in rows:
            det = d["details"]
            note = "ref_tests failed: %s; ref_edge failed: %s; mutants killed: %d/%d" % (
                ", ".join(det.get("ref_tests_failed", [])) or "-",
                ", ".join(det.get("ref_edge_failed", [])) or "-",
                sum(det.get("mutants_killed", {}).values()), n_mut)
            f.write("| %s | %s | %s | %s | %s | %s | %s. %s |\n" % (
                name, d["IC_tests"], d["IC_fix"], d["VC"], d["RC_tests"], d["RC_edge"], desc, note))
        f.write("\n## (f) Mutants vs smoke / ref_tests / ref_edge "
                "(`python3 private/check_variants.py`, exit %d)\n\n" % cv.returncode)
        f.write("Every mutant must fail at least one ref_edge case and no smoke case; gold "
                "must fail nothing; the original must pass every smoke case and fail every "
                "ref_edge case.\n\n```\n%s```\n" % cv.stdout)
        f.write("\n## Raw scorer output\n\n")
        for name, desc, d in rows:
            f.write("### %s\n\n```\n%s\n```\n\n" % (name, json.dumps(d, sort_keys=True)))


if __name__ == "__main__":
    main()
