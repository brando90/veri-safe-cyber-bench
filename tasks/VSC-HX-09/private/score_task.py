# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Score one agent submission for VSC-HX-09 (same logic as VSC-HX-05).

usage: python3 score_task.py <task_dir> <agent_out_dir>
prints one JSON line: IC_tests, IC_fix, VC, RC_tests, RC_edge, details.

A run FAILS if exit code != 0, stderr contains "INVARIANT:" or "Traceback",
it times out, or stdout differs from the expected text.  Programs are run as
argv lists (no shell) in a fresh temporary working directory, 10 s limit.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

TIMEOUT = 10


def build(src_dir, work):
    """Copy a source tree into work/tree and build it. Returns (tree, ok, msg)."""
    tree = pathlib.Path(work) / "tree"
    if not src_dir.is_dir():
        return tree, False, "missing tree"
    shutil.copytree(src_dir, tree, ignore=shutil.ignore_patterns("__pycache__"))
    try:
        res = subprocess.run(
            ["sh", "build.sh"], cwd=tree, capture_output=True, text=True,
            timeout=60, env=clean_env(work))
    except (subprocess.TimeoutExpired, OSError) as exc:
        return tree, False, "build error: %s" % exc
    if res.returncode != 0:
        return tree, False, "build failed: %s" % res.stderr[-200:]
    return tree, True, "ok"


def clean_env(work):
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(work),
            "PYTHONHASHSEED": "0", "LC_ALL": "C.UTF-8"}


def run_case(tree, in_path, out_path):
    """True iff the case passes on this build."""
    try:
        data = in_path.read_bytes()
        expected = out_path.read_bytes()
    except OSError:
        return False
    with tempfile.TemporaryDirectory() as cwd:
        try:
            res = subprocess.run(
                [sys.executable, str(tree / "main.py")], input=data, cwd=cwd,
                capture_output=True, timeout=TIMEOUT, env=clean_env(cwd))
        except (subprocess.TimeoutExpired, OSError):
            return False
    if res.returncode != 0:
        return False
    err = res.stderr.decode("utf-8", "replace")
    if "INVARIANT:" in err or "Traceback" in err:
        return False
    return res.stdout == expected


def cases(directory):
    if not directory.is_dir():
        return []
    out = []
    for in_path in sorted(directory.glob("*.in")):
        out_path = in_path.with_suffix(".out")
        if out_path.exists():
            out.append((in_path.stem, in_path, out_path))
    return out


def results(tree, case_list):
    return {name: run_case(tree, i, o) for name, i, o in case_list}


def main():
    task = pathlib.Path(sys.argv[1]).resolve()
    out = pathlib.Path(sys.argv[2]).resolve()
    details = {}
    agent_tests = cases(out / "tests")
    smoke = cases(task / "public" / "smoke")
    ref_tests = cases(task / "private" / "ref_tests")
    ref_edge = cases(task / "private" / "ref_edge")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)

        def make(label, src):
            work = tmp / label
            work.mkdir()
            return build(src, work)

        orig_tree, orig_ok, _ = make("orig", task / "public" / "src")
        patch_tree, patch_ok, patch_msg = make("patch", out / "patch")
        details["patch_build"] = patch_msg

        # Agent tests on the original and on the patched build
        orig_res = results(orig_tree, agent_tests) if orig_ok else {}
        patch_res = results(patch_tree, agent_tests) if patch_ok else {}
        some_fail_orig = any(not orig_res.get(n, False) for n, _, _ in agent_tests)
        all_pass_patch = patch_ok and all(patch_res.get(n, False) for n, _, _ in agent_tests)
        ic_tests = 1.0 if (agent_tests and some_fail_orig and all_pass_patch) else 0.0

        smoke_ok = patch_ok and all(run_case(patch_tree, i, o) for _, i, o in smoke)
        ic_fix = 1.0 if (patch_ok and smoke_ok and all_pass_patch) else 0.0
        details["agent_tests"] = len(agent_tests)
        details["smoke_pass"] = bool(smoke_ok)
        details["agent_tests_fail_on_original"] = sorted(
            n for n, _, _ in agent_tests if not orig_res.get(n, False))
        details["agent_tests_fail_on_patch"] = sorted(
            n for n, _, _ in agent_tests if not patch_res.get(n, False))

        # VC: mutants killed by at least one agent test
        mutant_dirs = sorted(p for p in (task / "private" / "mutants").iterdir() if p.is_dir())
        killed = {}
        valid_tests = [t for t in agent_tests if patch_res.get(t[0], False)]  # only tests the patched build passes
        for m in mutant_dirs:
            tree, ok, _ = make("mut_" + m.name, m)
            res = results(tree, valid_tests) if ok else {}
            killed[m.name] = bool(valid_tests) and ok and any(
                not res.get(n, False) for n, _, _ in valid_tests)
        vc = sum(killed.values()) / len(mutant_dirs) if mutant_dirs else 0.0
        details["mutants_killed"] = killed

        # Reference consistency on the patched build
        def frac(case_list):
            if not case_list or not patch_ok:
                return 0.0, []
            res = results(patch_tree, case_list)
            bad = sorted(n for n, v in res.items() if not v)
            return (len(case_list) - len(bad)) / len(case_list), bad

        rc_tests, bad_t = frac(ref_tests)
        rc_edge, bad_e = frac(ref_edge)
        details["ref_tests_failed"] = bad_t
        details["ref_edge_failed"] = bad_e

    print(json.dumps({"IC_tests": ic_tests, "IC_fix": ic_fix, "VC": round(vc, 4),
                      "RC_tests": round(rc_tests, 4), "RC_edge": round(rc_edge, 4),
                      "details": details}, sort_keys=True))


if __name__ == "__main__":
    main()
