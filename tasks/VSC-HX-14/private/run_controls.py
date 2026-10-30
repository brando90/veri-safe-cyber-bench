#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29. Adapted from HX-12.
"""Build the synthetic agent outputs (controls), run the real scorer on each,
check every mutant against smoke and ref_edge (control f), and write
CONTROLS.md with the real output.  Run build_private.sh first; it writes the
control patch trees (make_variants.py) and the expected outputs."""
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
SCORER = os.path.join(HERE, "score_task.py")
CT = os.path.join(HERE, "controls")
GOLD = os.path.join(HERE, "gold")
PUB = os.path.join(TASK, "public", "src")

sys.path.insert(0, HERE)
import check_variants  # noqa: E402
import score_task  # noqa: E402


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
    for sub in ("tests", "REPORT.md"):
        p = os.path.join(root, sub)
        if os.path.isdir(p):
            shutil.rmtree(p)
        elif os.path.exists(p):
            os.remove(p)
    os.makedirs(root, exist_ok=True)
    if patch_src is not None:
        if os.path.isdir(keep_patch):
            shutil.rmtree(keep_patch)
        shutil.copytree(patch_src, keep_patch, ignore=shutil.ignore_patterns("__pycache__"))
    if tests is not None:
        cp_tests(os.path.join(root, "tests"), tests)
        with open(os.path.join(root, "REPORT.md"), "w") as f:
            f.write("control %s\n" % name)
    return root


# one ref_edge case per variant (the fixed ones only for d)
ONE_EACH = ["e01_civil_leap_day_2000", "e03_category_backslash", "e05_varint_duration_values",
            "e07_offset_negative_minutes", "e09_weekly_every2_midweek_start",
            "e11_snap_carry_into_next_day", "e13_agenda_ties_multi_number_ids",
            "e15_reference_maximum", "e17_move_drops_stale_skips", "e19_title_long_blank_runs"]
FIXED_IN_D = [e for e in ONE_EACH if e[:3] not in ("e15", "e17")]

CONTROLS = [
    ("a_original", PUB, {"ref_edge": ["e01_civil_leap_day_2000"]},
     "(a) unpatched source as patch, plus one correct test"),
    ("b_gold", GOLD, {"ref_edge": all_edge(), "ref_tests": ["t07_count_includes_skips",
                                                          "t12_durations"]},
     "(b) gold as patch; every ref_edge plus two ref_tests as agent tests"),
    ("c_empty", None, None, "(c) empty out/"),
    ("d_partial", "keep", {"ref_edge": FIXED_IN_D},
     "(d) every defect fixed except the reference width at the maximum and the stale skips "
     "after an event move; one test per fixed defect"),
    ("e_overaggressive", "keep", {"ref_edge": ["e03_category_backslash"]},
     "(e) gold plus over-fixing: titles collapse every whitespace character (NBSP too), offset "
     "0 prints Z, a yearly Feb 29 event lands on Mar 1"),
    ("e2_overaggressive_listings", "keep", {"ref_edge": ["e01_civil_leap_day_2000"]},
     "(e2) gold plus over-fixing: busy merges only overlapping spans (touching spans stay "
     "apart), stale-skip pruning keeps the last skip"),
    ("g_check_disabled", "keep", {"ref_edge": ["e01_civil_leap_day_2000"]},
     "(g) all defects kept, self-check disabled (return at top of full_check)"),
]


def mutant_rows():
    groups = {"smoke": score_task.cases(pathlib.Path(TASK) / "public" / "smoke"),
              "ref_edge": score_task.cases(pathlib.Path(HERE) / "ref_edge")}
    rows = []
    for m in sorted(pathlib.Path(HERE, "mutants").iterdir()):
        res = check_variants.failing(m, groups)
        rows.append((m.name, res))
        print(m.name, json.dumps(res))
    return rows


def main():
    rows = []
    for name, patch, tests, desc in CONTROLS:
        root = mk_out(name, None if patch in (None, "keep") else patch, tests)
        if patch is None and os.path.isdir(os.path.join(root, "patch")):
            shutil.rmtree(os.path.join(root, "patch"))
        res = subprocess.run([sys.executable, SCORER, TASK, root], capture_output=True,
                             text=True, check=True)
        data = json.loads(res.stdout)
        rows.append((name, desc, data))
        print(name, res.stdout.strip())
    mrows = mutant_rows()
    nmut = len(mrows)
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
                sum(det.get("mutants_killed", {}).values()), nmut)
            f.write("| %s | %s | %s | %s | %s | %s | %s. %s |\n" % (
                name, d["IC_tests"], d["IC_fix"], d["VC"], d["RC_tests"], d["RC_edge"], desc, note))
        f.write("\n## (f) Mutants against smoke and ref_edge\n\n")
        f.write("Each mutant is gold with exactly one defect brought back "
                "(`python3 private/check_variants.py` gives the same data plus ref_tests).\n\n")
        f.write("| Mutant | smoke failed | ref_edge failed |\n|---|---|---|\n")
        for name, res in mrows:
            f.write("| %s | %s | %s |\n" % (name, ", ".join(res["smoke"]) or "none",
                                          ", ".join(res["ref_edge"]) or "NONE"))
        f.write("\n## Raw scorer output\n\n")
        for name, desc, d in rows:
            f.write("### %s\n\n```\n%s\n```\n\n" % (name, json.dumps(d, sort_keys=True)))


if __name__ == "__main__":
    main()
