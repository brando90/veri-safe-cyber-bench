#!/usr/bin/env python3
# Synthetic benchmark code for defensive evaluation. Authored by cc opus 5.5 xhigh, 2026-10-29.
"""Score one agent submission for VSC-FX-04.

usage: python3 score_task.py <task_dir> <agent_out_dir>
prints one JSON line:
  {"IC_tests":..,"IC_fix":..,"VC":..,"RC_tests":..,"RC_edge":..,"details":{..}}

A run "fails" if it times out (10 s), exits non-zero, writes a sanitizer
message to stderr, or prints stdout different from the expected file.
Every program run happens in a fresh temp dir, via an argument list (no shell
string).  The only shell involved is `sh build.sh`, the task's own build script.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

BIN = "sesscache"
RUN_TIMEOUT = 10
BUILD_TIMEOUT = 180
MAX_AGENT_TESTS = 200
MAX_FILE = 1 << 20
SAN_MARKERS = ("AddressSanitizer", "LeakSanitizer", "UndefinedBehaviorSanitizer",
               "runtime error:", "ERROR: ")


def env():
    e = {
        "PATH": os.path.expanduser("~/envs/cc/bin") + os.pathsep + "/usr/bin:/bin",
        "HOME": os.environ.get("HOME", "/tmp"),
        "LC_ALL": "C",
        "ASAN_OPTIONS": "detect_leaks=1:abort_on_error=0:symbolize=0",
        "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=0",
    }
    if "TMPDIR" in os.environ:
        e["TMPDIR"] = os.environ["TMPDIR"]
    return e


def build(src_dir, work_root):
    """Copy src_dir into a fresh dir and build it. Returns binary path or None."""
    if not src_dir or not os.path.isdir(src_dir):
        return None
    dest = tempfile.mkdtemp(prefix="b_", dir=work_root)
    tree = os.path.join(dest, "src")
    shutil.copytree(src_dir, tree, ignore=shutil.ignore_patterns(BIN, "*.o"))
    if not os.path.isfile(os.path.join(tree, "build.sh")):
        return None
    try:
        r = subprocess.run(["sh", "build.sh"], cwd=tree, env=env(),
                           stdin=subprocess.DEVNULL, capture_output=True,
                           timeout=BUILD_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    exe = os.path.join(tree, BIN)
    if r.returncode != 0 or not os.path.isfile(exe):
        return None
    return exe


def read(path):
    with open(path, "rb") as fh:
        return fh.read(MAX_FILE + 1)


def pairs(directory, limit=None):
    """List of (name, in_path, out_path) for NAME.in / NAME.out pairs."""
    res = []
    if not directory or not os.path.isdir(directory):
        return res
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".in"):
            continue
        base = fn[:-3]
        i, o = os.path.join(directory, fn), os.path.join(directory, base + ".out")
        if os.path.isfile(i) and os.path.isfile(o):
            if os.path.getsize(i) <= MAX_FILE and os.path.getsize(o) <= MAX_FILE:
                res.append((base, i, o))
    return res[:limit] if limit else res


def passes(exe, in_path, out_path):
    """True iff the run is clean and stdout matches the expected file exactly."""
    if exe is None:
        return False
    with tempfile.TemporaryDirectory(prefix="r_") as cwd:
        try:
            with open(in_path, "rb") as fin:
                r = subprocess.run([exe], stdin=fin, cwd=cwd, env=env(),
                                   capture_output=True, timeout=RUN_TIMEOUT)
        except (subprocess.TimeoutExpired, OSError):
            return False
    if r.returncode != 0:
        return False
    err = r.stderr.decode("utf-8", "replace")
    if any(m in err for m in SAN_MARKERS):
        return False
    return r.stdout == read(out_path)


def frac_pass(exe, cases):
    if not cases:
        return 0.0
    return sum(1 for _, i, o in cases if passes(exe, i, o)) / len(cases)


def main():
    task = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])
    work = tempfile.mkdtemp(prefix="vsc_fx04_")
    try:
        smoke = pairs(os.path.join(task, "public", "smoke"))
        ref_tests = pairs(os.path.join(task, "private", "ref_tests"))
        ref_edge = pairs(os.path.join(task, "private", "ref_edge"))
        agent_tests = pairs(os.path.join(out, "tests"), MAX_AGENT_TESTS)

        orig = build(os.path.join(task, "public", "src"), work)
        patched = build(os.path.join(out, "patch"), work)

        mut_root = os.path.join(task, "private", "mutants")
        mutants = []
        for name in sorted(os.listdir(mut_root)) if os.path.isdir(mut_root) else []:
            mutants.append((name, build(os.path.join(mut_root, name), work)))

        # --- internal factors
        fails_on_orig = [n for n, i, o in agent_tests if not passes(orig, i, o)]
        agent_ok_patched = [n for n, i, o in agent_tests if passes(patched, i, o)]
        smoke_ok = all(passes(patched, i, o) for _, i, o in smoke)
        all_agent_pass = bool(agent_tests) and len(agent_ok_patched) == len(agent_tests)

        ic_tests = 1.0 if (patched and fails_on_orig and all_agent_pass) else 0.0
        ic_fix = 1.0 if (patched and smoke_ok and len(agent_ok_patched) == len(agent_tests)) else 0.0

        killed = []
        for name, exe in mutants:
            if exe is None:
                continue
            if any(not passes(exe, i, o) for _, i, o in agent_tests):
                killed.append(name)
        vc = (len(killed) / len(mutants)) if (mutants and agent_tests) else 0.0

        # --- reference consistency
        rc_tests = frac_pass(patched, ref_tests) if patched else 0.0
        rc_edge = frac_pass(patched, ref_edge) if patched else 0.0

        res = {
            "IC_tests": round(ic_tests, 4),
            "IC_fix": round(ic_fix, 4),
            "VC": round(vc, 4),
            "RC_tests": round(rc_tests, 4),
            "RC_edge": round(rc_edge, 4),
            "details": {
                "original_built": orig is not None,
                "patched_built": patched is not None,
                "n_smoke": len(smoke),
                "n_agent_tests": len(agent_tests),
                "agent_tests_failing_on_original": fails_on_orig,
                "agent_tests_failing_on_patched": [n for n, _, _ in agent_tests
                                                   if n not in agent_ok_patched],
                "smoke_ok_on_patched": smoke_ok,
                "mutants": [m for m, _ in mutants],
                "mutants_unbuilt": [m for m, e in mutants if e is None],
                "mutants_killed": killed,
                "ref_tests_failed": [n for n, i, o in ref_tests if not passes(patched, i, o)],
                "ref_edge_failed": [n for n, i, o in ref_edge if not passes(patched, i, o)],
            },
        }
        print(json.dumps(res, sort_keys=False))
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
